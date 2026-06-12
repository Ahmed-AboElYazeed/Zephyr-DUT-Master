cmake_minimum_required(VERSION 3.20)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(testbench)

target_include_directories(app PRIVATE include)

target_sources(app PRIVATE
  src/main.c
  src/tb_gpio.c
  src/tb_pinmap.c
#   src/tb_adc.c
#   src/tb_spi.c
#   src/tb_uart.c
#   src/tb_pwm.c
#   src/tb_desc.c
)