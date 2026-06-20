*** Settings ***
Resource    resources/testbench.resource
Resource    resources/patterns_gpio.resource

Suite Setup       Open Testbench
Suite Teardown    Close Testbench
Test Teardown     Log UART History On Failure

*** Test Cases ***

GPIO drives high
    GPIO Set    PA5    1
    ${val}=    GPIO Get    PB3
    Should Be Equal As Integers    ${val}    1

GPIO drives low
    GPIO Set    PA5    0
    ${val}=    GPIO Get    PB3
    Should Be Equal As Integers    ${val}    0

GPIO toggle cycle
    GPIO Toggle And Verify    PA5    PB3    cycles=5

GPIO unknown pin raises error
    Run Keyword And Expect Error    *ERROR*    GPIO Get    BADPIN
