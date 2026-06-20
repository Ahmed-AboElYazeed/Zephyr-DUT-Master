*** Settings ***
Resource    resources/testbench.resource

Suite Setup       Open Testbench
Suite Teardown    Close Testbench
Test Teardown     Log UART History On Failure

*** Test Cases ***

SPI loopback single byte
    ${rx}=    SPI Transfer    0    AA
    Should Be Equal    ${rx}    AA

SPI loopback multi byte
    ${rx}=    SPI Transfer    0    DE    AD    BE    EF
    Should Be Equal    ${rx}    DE AD BE EF

SPI all zeros
    ${rx}=    SPI Transfer    0    00    00
    Should Be Equal    ${rx}    00 00

SPI all ones
    ${rx}=    SPI Transfer    0    FF    FF
    Should Be Equal    ${rx}    FF FF
