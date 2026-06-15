*** Settings ***
Resource    resources/testbench.resource

Suite Setup      Open Testbench
Suite Teardown   Close Testbench

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
    FOR    ${i}    IN RANGE    5
        GPIO Set    PA5    1
        ${h}=    GPIO Get    PB3
        Should Be Equal As Integers    ${h}    1
        GPIO Set    PA5    0
        ${l}=    GPIO Get    PB3
        Should Be Equal As Integers    ${l}    0
    END

GPIO unknown pin raises error
    Run Keyword And Expect Error    *ERROR*    GPIO Get    BADPIN
