#include <zephyr/kernel.h>
#include <zephyr/shell/shell.h>
#include <zephyr/shell/shell_uart.h>

int main(void)
{    
    printk("Testbench ready. Type 'help' or Start using 'tb'\n");
    return 0;
}