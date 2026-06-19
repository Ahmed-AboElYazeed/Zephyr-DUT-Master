*** Settings ***
Resource    resources/testbench.resource
Suite Setup      Open Testbench
Suite Teardown   Close Testbench
Test Setup       Motorsim Start
Test Teardown    Motorsim Stop

*** Test Cases ***

Motor responds to voltage command
    # DUT applies 3.3V (full voltage), no load
    Sleep    1s
    ${result}=    Motorsim Get
    Should Be True    ${result}[speed_rpm] > 0
    ...    msg=Speed should increase when voltage is applied

Motor speed drops under load
    Sleep    1s
    ${no_load}=    Motorsim Get
    # DUT now applies 10N load via its ADC output
    Sleep    1s
    ${loaded}=    Motorsim Get
    Should Be True    ${loaded}[speed_rpm] < ${no_load}[speed_rpm]
    ...    msg=Speed should drop under load

Steady-state speed within expected range
    Sleep    3s    # allow settling
    ${result}=    Motorsim Get
    Should Be True    400 <= ${result}[speed_rpm] <= 500
    ...    msg=At full voltage, no load, expected near-max speed
