*** Settings ***
Resource    resources/testbench.resource

Suite Setup       Open Testbench
Suite Teardown    Close Testbench

*** Variables ***
${SOAK_CYCLES}    1000

*** Test Cases ***

GPIO Soak 1000 Cycles
    [Tags]    soak    slow
    FOR    ${i}    IN RANGE    ${SOAK_CYCLES}
        GPIO Set    PA5    1
        ${h}=    GPIO Get    PB3
        Should Be Equal As Integers    ${h}    1
        GPIO Set    PA5    0
        ${l}=    GPIO Get    PB3
        Should Be Equal As Integers    ${l}    0
        IF    ${i} % 100 == 0
            Log    GPIO soak cycle ${i}/${SOAK_CYCLES}
        END
    END

ADC Stability Soak
    [Tags]    soak    slow
    ${readings}=    Create List
    FOR    ${i}    IN RANGE    ${SOAK_CYCLES}
        ${mv}=    ADC Read MV    PA0
        Append To List    ${readings}    ${mv}
    END
    ${min}=    Evaluate    min(${readings})
    ${max}=    Evaluate    max(${readings})
    ${spread}=    Evaluate    ${max} - ${min}
    Should Be True    ${spread} < 100
    ...    msg=ADC spread over ${SOAK_CYCLES} readings: ${spread} mV (min=${min}, max=${max})

SPI Loopback Soak
    [Tags]    soak    slow
    FOR    ${i}    IN RANGE    ${SOAK_CYCLES}
        ${rx}=    SPI Transfer    0    DE    AD
        Should Be Equal    ${rx}    DE AD
    END

UART Round-Trip Soak
    [Tags]    soak    slow
    FOR    ${i}    IN RANGE    ${SOAK_CYCLES}
        ${payload}=    Evaluate    'SOAK%06d' % ${i}
        UART Send    uart2    ${payload}
        ${rx}=    UART Recv    uart2    300
        Should Contain    ${rx}    ${payload}
    END
