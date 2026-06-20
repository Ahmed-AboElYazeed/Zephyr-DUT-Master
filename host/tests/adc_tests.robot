*** Settings ***
Resource    resources/testbench.resource
Resource    resources/patterns_gpio.resource

Suite Setup       Open Testbench
Suite Teardown    Close Testbench
Test Teardown     Log UART History On Failure

*** Test Cases ***

ADC reads valid range
    Assert ADC Within Range    PA0    0    3300

ADC reads expected voltage
    # PA0 connected to 1.65V (3.3V / 2 divider on the test fixture)
    ${mv}=    ADC Read MV    PA0
    Should Be True    abs(${mv} - 1650) < 100

ADC multiple readings are stable
    ${a}=    ADC Read MV    PA0
    ${b}=    ADC Read MV    PA0
    ${diff}=    Evaluate    abs(${a} - ${b})
    Should Be True    ${diff} < 50
