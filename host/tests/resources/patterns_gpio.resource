*** Settings ***
Resource    testbench.resource

*** Keywords ***

Assert GPIO Response To Stimulus
    [Documentation]    Drive stimulus_pin and assert response_pin reaches expected_level.
    [Arguments]    ${stimulus_pin}    ${stimulus_level}
    ...            ${response_pin}    ${expected_level}    ${settle_ms}=10
    GPIO Set    ${stimulus_pin}    ${stimulus_level}
    Sleep    ${settle_ms}ms
    ${actual}=    GPIO Get    ${response_pin}
    Should Be Equal As Integers    ${actual}    ${expected_level}
    ...    msg=Response pin ${response_pin} expected ${expected_level} got ${actual}

GPIO Toggle And Verify
    [Documentation]    Toggle a pin N times and verify each transition is echoed.
    [Arguments]    ${out_pin}    ${in_pin}    ${cycles}=10
    FOR    ${i}    IN RANGE    ${cycles}
        GPIO Set    ${out_pin}    1
        Sleep    5ms
        ${h}=    GPIO Get    ${in_pin}
        Should Be Equal As Integers    ${h}    1
        GPIO Set    ${out_pin}    0
        Sleep    5ms
        ${l}=    GPIO Get    ${in_pin}
        Should Be Equal As Integers    ${l}    0
    END
    Log    Completed ${cycles} toggle cycles on ${out_pin} -> ${in_pin}

Assert ADC Within Range
    [Documentation]    Read ADC pin and assert value is within [min_mv, max_mv].
    [Arguments]    ${pin}    ${min_mv}    ${max_mv}
    ${mv}=    ADC Read MV    ${pin}
    Should Be True    ${mv} >= ${min_mv} and ${mv} <= ${max_mv}
    ...    msg=ADC ${pin} read ${mv} mV, expected ${min_mv}-${max_mv} mV
    RETURN    ${mv}
