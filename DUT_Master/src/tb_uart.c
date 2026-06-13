#include <zephyr/shell/shell.h>
#include <zephyr/drivers/uart.h>
#include <zephyr/sys/ring_buffer.h>
#include <stdlib.h>

#define DUT_UART  DEVICE_DT_GET(DT_NODELABEL(usart2))
#define RX_BUF_SIZE 256

RING_BUF_DECLARE(uart_rx_ring, RX_BUF_SIZE);

static void uart_rx_isr(const struct device *dev, void *user_data)
{
    uint8_t c;
    while (uart_irq_update(dev) && uart_irq_rx_ready(dev)) {
        uart_fifo_read(dev, &c, 1);
        ring_buf_put(&uart_rx_ring, &c, 1);
    }
}

static int uart_init_dut(void)
{
    const struct device *uart = DUT_UART;
    if (!device_is_ready(uart)) {
        return -ENODEV;
    }
    uart_irq_callback_set(uart, uart_rx_isr);
    uart_irq_rx_enable(uart);
    return 0;
}
SYS_INIT(uart_init_dut, APPLICATION, 90);

int cmd_uart_send(const struct shell *sh, size_t argc, char **argv)
{
    if (argc < 3) {
        shell_error(sh, "ERROR: usage: tb uart send <dev> <string>");
        return -EINVAL;
    }
    /* argv[2] is the string; concatenate remaining args with spaces */
    const struct device *uart = DUT_UART;
    for (int i = 2; i < (int)argc; i++) {
        for (char *c = argv[i]; *c; c++) uart_poll_out(uart, *c);
        if (i < (int)argc - 1) uart_poll_out(uart, ' ');
    }
    uart_poll_out(uart, '\r');
    uart_poll_out(uart, '\n');
    shell_print(sh, "OK");
    return 0;
}

int cmd_uart_recv(const struct shell *sh, size_t argc, char **argv)
{
    if (argc != 3) {
        shell_error(sh, "ERROR: usage: tb uart recv <dev> <timeout_ms>");
        return -EINVAL;
    }
    int timeout_ms = atoi(argv[2]);
    uint8_t buf[128];
    uint32_t len = 0;
    int64_t deadline = k_uptime_get() + timeout_ms;

    while (k_uptime_get() < deadline) {
        uint32_t got = ring_buf_get(&uart_rx_ring, buf + len,
                                    sizeof(buf) - len - 1);
        len += got;
        if (len > 0 && buf[len-1] == '\n') break;
        k_sleep(K_MSEC(5));
    }

    if (len == 0) {
        shell_error(sh, "ERROR: timeout, no data");
        return -ETIMEDOUT;
    }
    buf[len] = '\0';
    shell_print(sh, "%s", buf);
    return 0;
}
