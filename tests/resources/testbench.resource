*** Settings ***
Library    ZephyrShellLib    port=${PORT}    baud=${BAUD}

*** Variables ***
${PORT}    /dev/ttyUSB0
${BAUD}    115200

*** Keywords ***
Open Testbench
    Log    Testbench connected on ${PORT}

Close Testbench
    Close
