PORT     ?= /dev/ttyUSB0
BAUD     ?= 115200
RESULTS  := results

PYTHONPATH=.

.PHONY: unit-test test test-gpio test-adc test-spi test-uart test-pwm test-motorsim test-soak clean

unit-test:
	pytest tests_unit/ -v

test:
	robot --outputdir $(RESULTS) \
	      --xunit $(RESULTS)/junit.xml \
	      --variable PORT:$(PORT) \
	      --variable BAUD:$(BAUD) \
	      --exclude soak \
	      tests/

test-gpio:
	robot --outputdir $(RESULTS) --variable PORT:$(PORT) tests/gpio_tests.robot

test-adc:
	robot --outputdir $(RESULTS) --variable PORT:$(PORT) tests/adc_tests.robot

test-spi:
	robot --outputdir $(RESULTS) --variable PORT:$(PORT) tests/spi_tests.robot

test-uart:
	robot --outputdir $(RESULTS) --variable PORT:$(PORT) tests/uart_tests.robot

test-pwm:
	robot --outputdir $(RESULTS) --variable PORT:$(PORT) tests/pwm_tests.robot

test-motorsim:
	robot --outputdir $(RESULTS) \
	      --variable PORT:$(PORT) \
	      --variable INPUT_SOURCE:$(or $(SOURCE),adc) \
	      --variable INPUT_PIN:$(or $(PIN),PA0) \
	      tests/motorsim_tests.robot

test-soak:
	robot --outputdir $(RESULTS)/soak --include soak --variable PORT:$(PORT) tests/soak_tests.robot

clean:
	rm -rf $(RESULTS) tests_unit/__pycache__ ZephyrShellLib/__pycache__
