*** Settings ***
Resource    testbench.resource
Resource    patterns_uart.resource

*** Variables ***
${DUT_RESET_PIN}    PB3
${DUT_POWER_PIN}    PB4
${BOOT_SETTLE_MS}   500

*** Keywords ***

Power On DUT
    [Documentation]    Assert power pin and wait for DUT to settle.
    GPIO Set    ${DUT_POWER_PIN}    1
    Sleep    ${BOOT_SETTLE_MS}ms

Power Off DUT
    GPIO Set    ${DUT_POWER_PIN}    0
    Sleep    100ms

Reset DUT
    [Documentation]    Pulse the reset line low then release.
    GPIO Set    ${DUT_RESET_PIN}    0
    Sleep    20ms
    GPIO Set    ${DUT_RESET_PIN}    1
    Sleep    ${BOOT_SETTLE_MS}ms

Power Cycle DUT
    Power Off DUT
    Sleep    200ms
    Power On DUT

Hard Reset And Wait For Banner
    [Arguments]    ${uart_dev}    ${banner}    ${timeout_ms}=3000
    Reset DUT
    ${response}=    UART Recv    ${uart_dev}    ${timeout_ms}
    Should Contain    ${response}    ${banner}
