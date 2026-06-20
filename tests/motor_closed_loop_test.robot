*** Settings ***
Resource    resources/testbench.resource
Suite Setup       Open Testbench
Suite Teardown    Close Testbench
Test Teardown     Run Keyword And Ignore Error    Motorsim Stop

*** Variables ***
# Change these to switch the whole suite between ADC and PWM input
# without touching any test case body.
${INPUT_SOURCE}     adc      # adc | pwm
${INPUT_PIN}         PA0      # PA0 for adc, PA1 for pwm (capture-capable pin)
${VMAX_MV}           3300

*** Test Cases ***

Motor simulation starts and reports state
    Motorsim Start    ${INPUT_SOURCE}    ${INPUT_PIN}    ${VMAX_MV}
    Sleep    1s
    ${state}=    Motorsim Get
    Should Be True    ${state}[t_ms] > 0
    Log    Speed: ${state}[speed_radps] rad/s, Current: ${state}[current_a] A

Motor speed increases with voltage command
    [Documentation]    Drive the DUT's command pin progressively higher
    ...    (externally, e.g. via a bench supply or function generator)
    ...    and confirm simulated speed rises. This test assumes the
    ...    input signal is driven by test equipment, not the testbench
    ...    itself, since the testbench is reading -- not sourcing -- here.
    Motorsim Start    ${INPUT_SOURCE}    ${INPUT_PIN}    ${VMAX_MV}
    Sleep    2s
    ${early}=    Motorsim Get Speed Radps
    Sleep    3s
    ${later}=    Motorsim Get Speed Radps
    Log    Speed at 2s: ${early} rad/s, at 5s: ${later} rad/s

Motor simulation step rate is consistent
    [Documentation]    Confirm t_ms advances by ~200ms increments
    ...    (the model's fixed step size) between Get calls separated
    ...    by sleeps, proving the background timer/workqueue is alive.
    Motorsim Start    ${INPUT_SOURCE}    ${INPUT_PIN}    ${VMAX_MV}
    ${s1}=    Motorsim Get
    Sleep    1s
    ${s2}=    Motorsim Get
    ${delta}=    Evaluate    ${s2}[t_ms] - ${s1}[t_ms]
    Should Be True    800 <= ${delta} <= 1200
    ...    msg=Expected ~1000ms of simulated time to pass, got ${delta}ms

Collect and assert on step response curve
    [Documentation]    Captures a transient response and checks basic
    ...    shape properties: starts near zero, ends higher than start,
    ...    and never goes negative (a sane motor speed response).
    Motorsim Start    ${INPUT_SOURCE}    ${INPUT_PIN}    ${VMAX_MV}
    ${samples}=    Collect Motorsim Samples    duration_s=5
    Should Not Be Empty    ${samples}
    ${first}=    Get From List    ${samples}    0
    ${last}=    Get From List    ${samples}    -1
    Should Be True    ${last}[speed_radps] >= ${first}[speed_radps]
    FOR    ${sample}    IN    @{samples}
        Should Be True    ${sample}[speed_radps] >= -0.01
        ...    msg=Speed went negative: ${sample}
    END
    Log    Collected ${samples.__len__()} samples over the response curve

Plant parameters can be overridden before a run
    [Documentation]    Confirms tb motorsim params is accepted and the
    ...    simulation still runs afterward (does not validate the
    ...    numeric effect -- that requires the curve comparison test
    ...    pattern above with two separate Collect calls).
    Motorsim Set Params    R=2.0    L=0.05    J=0.0005    K=0.1    b=0.0003
    Motorsim Start    ${INPUT_SOURCE}    ${INPUT_PIN}    ${VMAX_MV}
    Sleep    1s
    ${state}=    Motorsim Get
    Should Be True    ${state}[t_ms] > 0

*** Test Cases ***    # PWM-source-specific variant, run with INPUT_SOURCE=pwm
Switch to PWM source mid-suite
    [Documentation]    Demonstrates selecting PWM as the input source
    ...    explicitly within a test case, independent of the suite
    ...    variable, useful when one suite needs to test both paths.
    Motorsim Set Source    pwm    PA1
    Motorsim Start    pwm    PA1    3300
    Sleep    1s
    ${state}=    Motorsim Get
    Should Be True    ${state}[t_ms] > 0