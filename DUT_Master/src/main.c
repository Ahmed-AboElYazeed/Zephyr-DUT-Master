#include <zephyr/kernel.h>
#include <zephyr/shell/shell.h>
#include <zephyr/shell/shell_uart.h>
#include "tb_motorsim.h"

int main(void)
{    
    printk("Testbench ready. Type 'help' or Start using 'tb'\n");

    tb_motorsim_init();
    printk("Motor Simulation ready. Type 'help' or Start using 'motorsim'\n");
    return 0;
}