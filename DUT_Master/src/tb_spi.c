#include <zephyr/shell/shell.h>
#include <zephyr/drivers/spi.h>
#include <stdlib.h>

#define SPI_DEV  DEVICE_DT_GET(DT_NODELABEL(spi1))

static const struct spi_config spi_cfg = {
    .frequency = 1000000,
    .operation = SPI_WORD_SET(8) | SPI_TRANSFER_MSB | SPI_OP_MODE_MASTER,
};

/* Parse "DE AD BE EF" into byte array. Returns byte count, -1 on error. */
int parse_hex_args(size_t argc, char **argv, uint8_t *out, size_t max)
{
    int n = 0;
    for (size_t i = 0; i < argc && n < (int)max; i++, n++) {
        char *end;
        out[n] = (uint8_t)strtoul(argv[i], &end, 16);
        if (*end != '\0') return -1;
    }
    return n;
}

int cmd_spi_transfer(const struct shell *sh, size_t argc, char **argv)
{
    /* argv[1]=bus index (0), argv[2..] = hex bytes */
    if (argc < 3) {
        shell_error(sh, "ERROR: usage: tb spi xfer <bus> <byte_hex>...");
        return -EINVAL;
    }

    uint8_t tx_buf[64], rx_buf[64];
    int n = parse_hex_args(argc - 2, &argv[2], tx_buf, sizeof(tx_buf));
    if (n < 0) {
        shell_error(sh, "ERROR: invalid hex byte");
        return -EINVAL;
    }

    const struct spi_buf tx = { .buf = tx_buf, .len = n };
    const struct spi_buf rx = { .buf = rx_buf, .len = n };
    const struct spi_buf_set tx_set = { .buffers = &tx, .count = 1 };
    const struct spi_buf_set rx_set = { .buffers = &rx, .count = 1 };

    int ret = spi_transceive(SPI_DEV, &spi_cfg, &tx_set, &rx_set);
    if (ret < 0) {
        shell_error(sh, "ERROR: spi_transceive failed %d", ret);
        return ret;
    }

    for (int i = 0; i < n; i++) {
        shell_fprintf(sh, SHELL_NORMAL, "%02X", rx_buf[i]);
        if (i < n - 1) shell_fprintf(sh, SHELL_NORMAL, " ");
    }
    shell_print(sh, "");   /* newline */
    return 0;
}
