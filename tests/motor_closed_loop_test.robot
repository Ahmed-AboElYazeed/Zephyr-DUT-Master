*** Settings ***
Resource    resources/testbench.resource
Suite Setup      Open Testbench
Suite Teardown   Close Testbench
Test Setup       Motorsim Start
Test Teardown    Motorsim Stop

*** Variables ***
${REF_SPEEDS}           ${{[0, 60, 150, 400, 350]}}
${SETPOINT_DURATION}    ${6.0}
${CHECK_INTERVAL}       ${1.0}
${ERROR_LIMIT_RPM}      ${10.0}
${LOAD_TORQUE_NM}       ${0.0}

*** Test Cases ***
Motor Closed-Loop Step Response
    ${result_string}=    Run Motor Test Sequence
    ...    ref_speeds=${REF_SPEEDS}
    ...    setpoint_duration_s=${SETPOINT_DURATION}
    ...    check_interval_s=${CHECK_INTERVAL}
    ...    error_limit_rpm=${ERROR_LIMIT_RPM}
    ...    load_nm=${LOAD_TORQUE_NM}
    
    Log    ${result_string}    # "PASS PASS PASS FAIL PASS ..."
    
    ${pass_count}=    Get Pass Fail Count
    Should Be True    ${pass_count}[pass] > ${pass_count}[fail]
