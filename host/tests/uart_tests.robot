*** Settings ***
Resource    resources/testbench.resource
Resource    resources/patterns_uart.resource

Suite Setup       Open Testbench
Suite Teardown    Close Testbench
Test Teardown     Log UART History On Failure

*** Test Cases ***

UART loopback single message
    UART Send    uart2    hello
    ${rx}=    UART Recv    uart2    200
    Should Contain    ${rx}    hello

UART loopback stress
    UART Loopback Stress    uart2    iterations=20

UART receive timeout when nothing sent
    Run Keyword And Expect Error    *ERROR*    UART Recv    uart2    200
