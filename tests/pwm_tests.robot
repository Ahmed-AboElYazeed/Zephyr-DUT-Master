*** Settings ***
Resource    resources/testbench.resource
Suite Setup      Open Testbench
Suite Teardown   Close Testbench

*** Variables ***
${FREQ_TOLERANCE}    20      # Hz
${DUTY_TOLERANCE}    3       # percent

*** Test Cases ***

PWM 1kHz 50pct output and capture
    PWM Set    PA8    1000    50
    Sleep    0.1s
    ${result}=    PWM Capture    PA1
    Should Be True    abs(${result}[freq_hz] - 1000) < ${FREQ_TOLERANCE}
    Should Be True    abs(${result}[duty_pct] - 50)   < ${DUTY_TOLERANCE}

PWM 10kHz 25pct
    PWM Set    PA8    10000    25
    Sleep    0.1s
    ${freq}=    PWM Get Freq    PA1
    ${duty}=    PWM Get Duty    PA1
    Should Be True    abs(${freq} - 10000) < 100
    Should Be True    abs(${duty} - 25) < ${DUTY_TOLERANCE}

PWM duty sweep
    FOR    ${duty}    IN    10    25    50    75    90
        PWM Set    PA8    1000    ${duty}
        Sleep    0.05s
        ${measured}=    PWM Get Duty    PA1
        Should Be True    abs(${measured} - ${duty}) < ${DUTY_TOLERANCE}
    END
