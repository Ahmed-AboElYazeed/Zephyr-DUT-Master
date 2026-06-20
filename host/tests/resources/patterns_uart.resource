*** Settings ***
Resource    testbench.resource

*** Keywords ***

UART Command Response
    [Documentation]    Send a command to DUT and assert the response matches a pattern.
    [Arguments]    ${dev}    ${command}    ${expected_pattern}    ${timeout_ms}=500
    UART Send    ${dev}    ${command}
    ${response}=    UART Recv    ${dev}    ${timeout_ms}
    Should Match Regexp    ${response}    ${expected_pattern}
    ...    msg=UART response to '${command}' did not match '${expected_pattern}'
    RETURN    ${response}

UART Boot Sequence Check
    [Documentation]    Reset the DUT via GPIO and wait for its boot banner on UART.
    [Arguments]    ${reset_pin}    ${uart_dev}    ${boot_banner}    ${timeout_ms}=3000
    GPIO Set    ${reset_pin}    0
    Sleep    50ms
    GPIO Set    ${reset_pin}    1
    ${banner}=    UART Recv    ${uart_dev}    ${timeout_ms}
    Should Contain    ${banner}    ${boot_banner}
    ...    msg=DUT boot banner not found. Got: ${banner}

UART Loopback Stress
    [Documentation]    Send N strings and verify each echoes correctly.
    [Arguments]    ${dev}    ${iterations}=20
    FOR    ${i}    IN RANGE    ${iterations}
        ${payload}=    Evaluate    'TEST%04d' % ${i}
        UART Send    ${dev}    ${payload}
        ${rx}=    UART Recv    ${dev}    300
        Should Contain    ${rx}    ${payload}
    END
