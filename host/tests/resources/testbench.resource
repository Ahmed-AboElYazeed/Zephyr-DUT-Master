*** Settings ***
Library    ZephyrShellLib
...        port=${PORT}
...        baud=${BAUD}
...        timeout=${TIMEOUT}
...        retries=${RETRIES}
...        logdir=${UART_LOGDIR}

*** Variables ***
${PORT}           /dev/ttyUSB0
${BAUD}           115200
${TIMEOUT}        5.0
${RETRIES}        1
${UART_LOGDIR}    ${OUTPUT_DIR}/uart_logs

*** Keywords ***
Open Testbench
    Log    Testbench connected on ${PORT} @ ${BAUD} baud

Close Testbench
    Close

Log UART History On Failure
    [Documentation]    Wire this into Test Teardown to automatically
    ...    dump the last UART exchanges to the log when a test fails.
    Run Keyword If Test Failed
    ...    Run Keyword And Ignore Error
    ...    Log Last Uart Exchanges

Log Last Uart Exchanges
    ${history}=    Get Uart History    last_n=10
    Log    ${history}    level=WARN
