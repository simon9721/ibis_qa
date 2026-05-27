## IBIS QUALITY SPECIFICATION 

## Version 3.0 

## Ratified September 15, 2023 

IBIS Quality Specification Version 3.0 

Page 1 

## **Purpose** 

This document is a specification covering a methodology to enhance the quality of electronic component model files produced in conformance with the I/O Buffer Information Specification (IBIS) Version 7.2. More information on the IBIS specification can be found on the IBIS web page: 

https://www.ibis.org 

The purpose of the IBIS Specification is to provide a standard for model data exchange and thus to enhance the value of modeling and simulation. 

The purpose of this IBIS Quality Specification is to provide a methodology for validating model data against the IBIS Specification and a means of objective measures of correlating model simulation results with measurements or other model simulations. By providing standards for validating, correlating, and replicating simulation results we seek to enhance the value of modeling and simulation. 

Adherence to the directions in this document does not guarantee quality. They serve to enhance the exchange of data. The quality of models and simulations is largely the result of market forces. 

This IBIS Quality Specification is intended to supplement existing support mechanisms for producers of IBIS files. Email reflectors for IBIS community support are open to the public. Details on the email reflectors and the model review service offered by the IBIS Open Forum are described at the web URL given above. 

## **Revision History** 

Version 1.0 of this IBIS Quality Specification was released in November of 2004. 

Efforts from August of 2006 to August of 2009 have culminated in a significantly changed specification, released as Version 2.0. The quality level and correlation score numbering and lettering system has changed from Version 1.0. The check numbers have also changed, and checks overlapping with the IBISCHK program have been removed from the IBIS Quality Specification. 

Version 3.0 added requirements related to Level 4 – Suitable for Power-aware analysis. These include requirements for [Pin Mapping], [ISSO *], and [Composite Current] sections. 

## **Terms used in this document** 

- IBISCHK – The IBISCHK file checker program, sometimes referred to as the Golden Parser, is found at https://www.ibis.org/ibischk7/. 

- Vcc – Used in this document, the supply voltage value for an I/O buffer. This value might be represented in the [Voltage Range] or [Pullup Reference] keywords. 

IBIS Quality Specification Version 3.0 

Page 2 

## **Table of Contents** 

|**Table**|**of Contents**|
|---|---|
|1.|IBIS Quality Designator ................................................................................................................. 7|
|1.1|IBIS Quality Level Definitions ........................................................................................................ 7|
|1.1.1|IQ0 – Not Checked ........................................................................................................................ 7|
|1.1.2|IQ1 – Passes IBISCHK .................................................................................................................... 7|
|1.1.3|IQ2 – Suitable for Waveform Simulation ...................................................................................... 8|
|1.1.4|IQ3 – Suitable for Timing Analysis ................................................................................................ 8|
|1.1.5|IQ4 – Suitable for Power-Aware Analysis ..................................................................................... 8|
|1.2|Special Designators ....................................................................................................................... 8|
|1.2.1|Designator “G” – Contains Golden Waveforms ............................................................................ 8|
|1.2.2|Designator "M" – Measurement Correlated ................................................................................ 8|
|1.2.3|Designator "S" – Simulation Correlated ....................................................................................... 9|
|1.2.4|Designator "X" - Exceptions .......................................................................................................... 9|
|1.3|OPTIONAL Checks ......................................................................................................................... 9|
|1.4|IBIS Quality Summary ................................................................................................................... 9|
|2.|General Header Section Requirements ...................................................................................... 10|
|2.1|{LEVEL 1} IBIS file passes IBISCHK ............................................................................................... 10|
|3.|Component Section .................................................................................................................... 11|
|3.1|Component Package Requirements ........................................................................................... 11|
|3.1.1|{LEVEL 2} [Package] must have typ/min/max values ................................................................. 11|
|3.1.2|{LEVEL 2} [Package] model values must be reasonable ............................................................. 11|
|3.1.3|{LEVEL 4} Package model includes power and ground pins ....................................................... 12|
|3.1.4|{LEVEL 4} On-die and on-package decoupling included ............................................................. 13|
|3.2|Component Pin Requirements ................................................................................................... 13|
|3.2.1|{LEVEL 2} [Pin] section complete ................................................................................................ 13|
|3.2.2|{LEVEL 3} [Pin] RLC values are present and reasonable ............................................................. 14|
|3.3|Component Diff Pin Requirements ............................................................................................. 14|
|3.3.1|{LEVEL 2} [Diff Pin] referenced pin models match...................................................................... 14|
|3.3.2|{LEVEL 3} [Diff Pin] Vdiff and Tdelay_* complete and reasonable ............................................. 14|
|3.4|Component Pin Mapping Requirements .................................................................................... 14|
|3.4.1|{LEVEL 4} [Pin Mapping] section is included for each component ............................................. 14|
|3.4.2|{LEVEL 4} [Pin Mapping] table includes power and ground pins ................................................ 15|
|3.4.3|{LEVEL 4}   Specify [Merged Pins] keyword if applicable ............................................................ 15|



IBIS Quality Specification Version 3.0 

Page 3 

|4.|[Model Selector] Section ............................................................................................................ 15|
|---|---|
|4.1|{LEVEL 2} [Model Selector] entries have reasonable descriptions ............................................. 15|
|4.2|{LEVEL 2} Default [Model Selector] entries are consistent ......................................................... 15|
|5.|Model Section ............................................................................................................................. 16|
|5.1|Model General Requirements .................................................................................................... 16|
|5.1.1|{LEVEL 2} [Model] parameters have correct typ/min/max order .............................................. 16|
|5.1.2|{LEVEL 2} [Model] C_comp is reasonable ................................................................................... 16|
|5.1.3|{LEVEL 2} [Temperature Range] is reasonable ........................................................................... 17|
|5.1.4|{LEVEL 2} [Voltage Range] or [* Reference] is reasonable ......................................................... 17|
|5.2|Model Switching Behavior Requirements .................................................................................. 18|
|5.2.1|{LEVEL 3} [Model] Vinl and Vinh reasonable .............................................................................. 18|
|5.2.2|{LEVEL 3} [Model Spec] Vinl and Vinh reasonable ...................................................................... 18|
|5.2.3|{LEVEL 3} [Model Spec] Vinl+/- and Vinh+/- complete and reasonable ..................................... 19|
|5.2.4|{OPTIONAL} [Model Spec] Pulse subparameters complete ....................................................... 19|
|5.2.5|{LEVEL 2} [Model Spec] S_Overshoot subparameters complete and match data sheet ........... 19|
|5.2.6|{LEVEL 2} [Model Spec] S_Overshoot subparameters track typ/min/max ................................ 19|
|5.2.7|{LEVEL 2} [Model Spec] D_Overshoot_* subparameters complete and match data sheet ....... 19|
|5.2.8|{LEVEL 2} [Model Spec] D_Overshoot_* subparameters track typ/min/max ............................ 20|
|5.2.9|{LEVEL 3} [Receiver Thresholds] Vth present and matches data sheet, if needed ..................... 20|
|5.2.10|{LEVEL 3} [Receiver Thresholds] Vth_min and Vth_max present and match data sheet, if|
|needed 20||
|5.2.11|{LEVEL 3} [Receiver Thresholds] Vinh_ac, Vinl_ac present and match data sheet, if needed ... 20|
|5.2.12|{LEVEL 3} [Receiver Thresholds] Vinh_dc, Vinl_dc present and match data sheet, if needed ... 21|
|5.2.13|{LEVEL 3} [Receiver Thresholds] Tslew_ac/Tdiffslew_ac present and match data sheet, if|
|needed 21||
|5.2.14|{LEVEL 3} [Receiver Thresholds] Threshold_sensitivity and Ext_ref present and match data|
|sheet, if needed .......................................................................................................................................... 21||
|5.3|Model I-V Table Requirements ................................................................................................... 21|
|5.3.1|{LEVEL 2} I-V tables have correct typ/min/max order ................................................................ 22|
|5.3.2|{LEVEL 2} [Pullup] voltage sweep range is correct ..................................................................... 22|
|5.3.3|{LEVEL 2} [Pulldown] voltage sweep range is correct ................................................................. 22|
|5.3.4|{LEVEL 2} [POWER Clamp] voltage sweep range is correct ........................................................ 22|
|5.3.5|{LEVEL 2} [GND Clamp] voltage sweep range is correct ............................................................. 23|
|5.3.6|{LEVEL 2} I-V tables do not exhibit stair-stepping ...................................................................... 23|



IBIS Quality Specification Version 3.0 

Page 4 

|5.3.7|{LEVEL 2} Combined I-V tables are monotonic ........................................................................... 23|
|---|---|
|5.3.8|{LEVEL 2} [Pulldown] I-V tables pass through zero/zero ............................................................ 23|
|5.3.9|{LEVEL 2} [Pullup] I-V tables pass through zero/zero ................................................................. 23|
|5.3.10|{LEVEL 2} No leakage current in clamp I-V tables ....................................................................... 23|
|5.3.11|{LEVEL 2} I-V behavior not double-counted ............................................................................... 24|
|5.3.12|{LEVEL 2} On-die termination modeling documented ................................................................ 24|
|5.3.13|{LEVEL 2} ECL models I-V tables swept from -Vcc to +2 * Vcc. ................................................... 24|
|5.3.14|{LEVEL 2} Point distributions in I-V tables should be sufficient .................................................. 24|
|5.4|Model V-T Table Requirements .................................................................................................. 24|
|5.4.1|{LEVEL 2} Output and I/O buffers have sufficient V-T tables...................................................... 24|
|5.4.2|{LEVEL 2} V-T tables have reasonable point distribution ........................................................... 25|
|5.4.3|{LEVEL 3} V-T table duration is not excessive ............................................................................. 25|
|5.4.4|{LEVEL 2} V-T table endpoints match fixture voltages................................................................ 25|
|5.5|Model [Ramp] Data Requirements ............................................................................................. 26|
|5.5.1|{LEVEL 2} [Ramp] R_load present if value other than 50 ohms.................................................. 26|
|5.5.2|{LEVEL 2} [Ramp] typ/min/max order is correct ......................................................................... 26|
|5.5.3|{LEVEL 2} [Ramp] dV value is consistent with I-V table calculations .......................................... 26|
|5.5.4|{LEVEL 2} [Ramp] dt is consistent with 20%-80% crossing time ................................................. 26|
|5.6|Output Timing Checks ................................................................................................................. 27|
|5.6.1|{LEVEL 3} [Model Spec] Vmeas and Vref used if typ/min/max variation ................................... 27|
|5.6.2|{LEVEL 3} Vref consistent for Open-drain, Open-source, and ECL Model_types ....................... 27|
|5.7|Model ISSO Table Requirements ................................................................................................ 27|
|5.7.1|{LEVEL 4} All output-capable models include [ISSO PU] and [ISSO PD] tables ........................... 27|
|5.7.2|{LEVEL 4} ISSO tables have correct typ/min/max order ............................................................. 27|
|5.7.3|{LEVEL 4} ISSO tables have sufficient point distribution ............................................................ 28|
|5.7.4|{LEVEL 4} ISSO tables voltage sweep range is correct ................................................................ 28|
|5.8|Model I-T Table Requirements ................................................................................................... 28|
|5.8.1|{LEVEL 4} Each [Rising Waveform] and [Falling Waveform] table includes a [Composite|
|Current]|table .............................................................................................................................................. 28|
|5.8.2|{LEVEL 4} [Composite Current] waveform data points cover the same time range as the|
|corresponding V-T waveforms .................................................................................................................... 28||
|5.8.3|{LEVEL 4} [Composite Current] waveforms must be time-aligned with corresponding V-T|
|waveforms .................................................................................................................................................. 28||
|5.8.4|{LEVEL 4} [Composite Current] includes pre-driver behavior..................................................... 28|



IBIS Quality Specification Version 3.0 

Page 5 

|5.8.5|{LEVEL 4} Start and end points [Composite Current] values correlate with pullup and pulldown|
|---|---|
|tables|29|
|5.8.6|{LEVEL 4} [Composite Current] data includes current from correct voltage rails ...................... 29|
|5.8.7|{LEVEL 4} [Composite Current] curve is flat at start and end ..................................................... 29|
|5.8.8|{LEVEL 4} [Composite Current] table values should start or end at 0 when V_fixture = 0 ......... 29|
|6.|Correlation .................................................................................................................................. 30|
|Appendix|A – Smoothness checking algorithm ........................................................................................... 31|



IBIS Quality Specification Version 3.0 

Page 6 

## 1. IBIS Quality Designator 

The quality of an IBIS file can be determined by checking its data for correctness, and by correlating the data to a reference. Correctness is defined as conforming to a designated version of the IBIS 

Specification and the component data sheet. The checks defined in this document are performed to find the overall file quality. The quality score is represented with a designator such as “IQ3S”, for example, which would indicate that data for basic simulation and timing analysis have been checked, and the IBIS model has been correlated to a reference simulation. The summary IBIS Quality designator is embedded in the IBIS file as a comment or in the [Notes] section. 

## 1.1 IBIS Quality Level Definitions 

The quality level is defined as a combination of correctness checks and correlation checks. The correctness level is a number, and other special designations such as correlation are shown as appended letters. Some examples: 

- IQ0 - No IQ checking at all 

- IQ1 - Passes IBISCHK without errors or unexplained warnings 

- IQ2 - IQ1 + data for basic simulation checked 

- IQ3 - IQ2 + data for timing analysis checked 

- IQ4 - IQ3 + data for power-aware analysis checked 

- IQ3M - IQ3 + correlated against hardware measurements 

- IQ3MS  - IQ3 + correlated against measurements and simulation 

- IQ3GS - IQ3 + golden waveforms + correlated against simulation 

- IQ4X - IQ4, but exception(s) to check(s) commented in file 

The 5 recognized levels of correctness checks and 3 levels of correlation checks are discussed below. Details of the referenced checks and correlation tests are given in sections 2 through 7. 

## 1.1.1 IQ0 – Not Checked 

An IQ0 file has not been checked, or at least the checking has not been documented. This is a placeholder level useful for showing which files are queued for checking. Tools that create IBIS files should put IQ0 comments in the files. 

## 1.1.2 IQ1 – Passes IBISCHK 

An IQ1 file has been checked with the latest IBISCHK parser at the time of checking. 

- The version of IBISCHK used must be documented in the Quality Summary. 

- IBISCHK must report zero errors. 

- All IBISCHK warnings must be explained if they cannot be eliminated. Ideally, there should be no warnings, but it is recognized that some warnings cannot be eliminated. The IQ X designator 

IBIS Quality Specification Version 3.0 

Page 7 

should be used if any remaining warning would warrant the model user’s attention. For example, comments might specify special simulator setting requirements. 

## 1.1.3 IQ2 – Suitable for Waveform Simulation 

An IQ2 file can be simulated with reasonable assurance that the buffer signal waveforms are correct. It does not necessarily have accurate per-pin or coupled package modeling, may not have information needed to check timing, and may not have information to help measure power currents. IQ2 includes all items in IQ1, plus all items designated “{LEVEL 2}”. 

## 1.1.4 IQ3 – Suitable for Timing Analysis 

An IQ3 file is suitable for signal timing analysis. Package modeling at the pin level is present and accurate, and special keywords for measuring timing are present and correct. Coupled package modeling is not required. IQ3 includes all items in IQ2, plus all items designated “{LEVEL 3}”. 

## 1.1.5 IQ4 – Suitable for Power-Aware Analysis 

An IQ4 file is suitable for power-aware analysis. The power and ground currents associated with groups of buffers are accurately modeled. This is an extension of the signal analysis capabilities addressed by IQ2 and IQ3. 

## 1.2 Special Designators 

The following special designator letters can be appended to the IQ level to convey additional important information. 

## 1.2.1 Designator “G” – Contains Golden Waveforms 

Special designator “G” indicates that the file contains golden waveforms, the [Test Data] and [Test Load] keywords defined in IBIS 4.0. Users can compare simulations of IBIS buffer models with the same test loads against the corresponding golden waveforms. Golden waveforms must be produced from source simulations or measurements, not from simulations of IBIS models. The set of [Test Load] fixtures used must include at least one with a transmission line. The “G” designator may be used with IBIS files containing golden waveforms for only a subset of buffer models, as determined by sound engineering judgment. 

## 1.2.2 Designator "M" – Measurement Correlated 

Special designator "M" indicates that measurement correlation has been performed and the results are deemed satisfactory. The “M” designator may be used with IBIS files containing golden waveforms for only a subset of buffer models, as determined by sound engineering judgment. More on correlation can be found in section 6. 

IBIS Quality Specification Version 3.0 

Page 8 

## 1.2.3 Designator "S" – Simulation Correlated 

Special designator "S" indicates that simulation correlation has been performed and the results are deemed satisfactory. The “S” designator may be used with IBIS files containing golden waveforms for only a subset of buffer models, as determined by sound engineering judgment. More on correlation can be found in section 6. 

## 1.2.4 Designator "X" - Exceptions 

Special designator "X" refers to exception from correctness or correlation. Exceptions should be used to declare that the file is suitable for the purpose indicated by the IQ level even though one or more checks are not passed by strict standards. The reason for the exception must be documented in the [Notes] section. Before using an IBIS file with the X designator in its IQ score, the model user should open the file and look for comments explaining exceptions. 

## 1.3 OPTIONAL Checks 

A limited number of IQ checks have {OPTIONAL} in the title instead of a {LEVEL n} designator. While considered good practice, these checks are not required to achieve any IQ level. This is generally used where data is not commonly available in suitable form for the IBIS representation. 

## 1.4 IBIS Quality Summary 

The summary IQ score for an IBIS file is determined as follows: 

- The summary IQ level number is the highest for which all checks of that level are passed. 

- “M”, “S”, and/or “G” designators are appended to the summary IQ score if a reasonable set of models have been measurement and/or simulation correlated, or if the file contains golden waveforms, respectively. 

- “X” is appended to the summary IQ score if any check in the file cannot be passed without exception. 

- OPTIONAL checks have no effect on the summary IQ score. 

The summary IQ score must be written in the IBIS file. This should appear in the [Notes] section, but comment lines are acceptable. Any exceptions must also be explained in the IBIS file. An example IQ summary in an IBIS file might look like this: 

- `|IQ Score: IQ3SX` 

- `|IQ Exception: Correlation not performed for untimed low speed signals.` 

The pass/fail status of individual IQ checks may be posted in the file as comments or contained in a separate document such as an IBIS file quality report. The latter is preferred, especially if the report also contains details such as waveforms, correlation metrics, and reviewer’s notes. For each check the ID number and IQ level of the check should be stated, along with the name of any [Component] or [Model] to which it applies, as well as the pass/fail status. 

IBIS Quality Specification Version 3.0 

Page 9 

## 2. General Header Section Requirements 

Requirements for the header section of the IBIS file, from the beginning of the file to the line before the first [Component] keyword. 

## 2.1 {LEVEL 1} IBIS file passes IBISCHK 

IBIS models are expected to pass the checks performed by the IBISCHK program before they are released to the public. Passing IBISCHK ensures that the file will attain at least an IQ1 level designation. 

A best practice is to insert the full output from the IBISCHK program into the IBIS file as comments, with explanation for any warnings annotated within. When doing this it is important to ensure that the added comments do not cause new “line too long” IBISCHK warnings. 

In general, it is best to use the latest available version of the IBISCHK program, as the latest version may include new tests and fixes for bugs found in the older versions. The IBISCHK program used must, at a minimum, be able to accommodate the [IBIS Ver] of the IBIS file at hand. The [IBIS Ver] used in the IBIS file is set by the model maker based on the set of IBIS keywords required to represent the behavior of the part completely and correctly. 

Some IBISCHK warnings may be permissible due to special circumstances regarding the model, but they must be identified in the IBIS file itself in the [Notes] section of the file. The warnings, along with the reason why they should be considered acceptable must be identified. Also, the IQ level designator must include “X” for exceptions due to warnings. 

The X (exception) designation is used to document all exception cases that might be important to some users. These would mostly apply to warning messages where the model provider gives further information. The X designation may also apply to cases where the extracted or specification information has been changed. The model provider should describe the impact of this change. Finally, it can also be used for any unusual situation in the parser, where the model information is correct, but the parser still issues warning or caution messages. The main point is that the model provider has purposely issued the model with some deviation, and the user needs to know about its details to understand the issues that might arise in using the model. 

For some minor deviations including where model data is changed to eliminate warning messages, the X designation might not be needed. For example, the X would normally not be used for I-V table regions where some non-monotonic data due to measurement noise or spurious data is removed. The changed data has minimal impact on model simulations and helps increase model portability. 

Occasionally a problem exists with IBISCHK rather than with the model. While the IBISCHK problem may be fixed in the future, the existing model could be tagged with X and contain a description of its issues and how this may impact how the IBIS model is used. In the event an error is generated due to a specific bug in the IBISCHK, intentional deviation in the model may be permitted to suppress the error in the model, provided such deviations are properly documented in the [Notes] section with “X” tagged in the quality designation. This suppression of an error is a unique case and should have minimal impact on the accuracy of the model. 

IBIS Quality Specification Version 3.0 

Page 10 

A Level 1 Model must NOT produce ANY errors when run through IBISCHK. 

Summary: 

- The goal is zero errors and zero warnings. 

- In some cases, zero warnings are not possible. 

- Add the “X” designator to the IQ level if there are warnings. 

- Document known cases of acceptable warnings. 

- Document the version of IBISCHK used. 

- Include a list of past File Rev/Dates and the reason for each model change. 

## 3. Component Section 

Checks for the [Component] section may be waived for IBIS files for programmable parts such as FPGAs, if the file is generic in nature, and does not represent a final, programmed part. In generic IBIS files the [Pin] section typically contains one entry for each [Model], but it does not correspond to any actual device pin map. 

## 3.1 Component Package Requirements 

Requirements for the [Package] and [Package Model] sections: 

## 3.1.1 {LEVEL 2} [Package] must have typ/min/max values 

The IBIS specification requires typical values in the [Package] keywords and allows minimum and maximum values to be NA if not available. To achieve IQ level 2 an IBIS file must have typical, minimum, and maximum values in the [Package] keywords. A reflection analysis based only on typical package model is likely to be optimistic. Minimum and maximum values are required to ensure that peak distortion levels are predicted. 

## 3.1.2 {LEVEL 2} [Package] model values must be reasonable 

Reasonable values for signal pins are L < 100 nH, C < 100 pF, R < 10 ohm. Minimum must be less than typical and typical less than maximum. 

The IBISCHK program detects typographical errors such as omitting the scaling factor following a number value, by checking against higher limits: L < 1000 nH, C < 1000 pF, R < 50 ohm. An R_pkg value of 1000 would easily fail this test, for example. This IQ check, with its lower limits, will detect other errors such as extra digits or measurement error. 

The minimum and maximum values of these parameter values should represent the range spanned by the actual pin parameter values for signal pins. The typical values should fall between the minimum and maximum values; typically, it is the average of the signal pin values, but it need not be. Methods and assumptions used, such as whether power and ground pins are included in the determination of the [Package] model values, should be documented as comments. 

IBIS Quality Specification Version 3.0 

Page 11 

L and C values might be used in the EDA tool to create a transmission-line model or might be left as discrete L and C elements. The EDA tool might connect the discrete L and C elements in a series, T, or pi topology. The model changes the simulation results. The model creator should add a comment in the file to state the preferred modeling method. The model user might then select the appropriate model option in the EDA tool. 

## 3.1.3 {LEVEL 4} Package model includes power and ground pins 

The assigned package model includes power pins with coupling between signals, power, and ground. The package model might be defined by keywords: 

- [Define Package Model] 

- [External Circuit] (not preferred) 

- [Interconnect Model] (including IBIS-ISS and Touchstone files) 

- [EMD Model] 

These sections should not be mixed in the same component since this situation causes confusion for the model user and possibly for the EDA tool. 

The model comments should explain the package modeling method. 

|**Model Type **|**Pro**|**Con**|
|---|---|---|
|**[Define Package Model]**|Details for long pin<br>interconnect|Coupled, single-stage, lumped* OR T-lines with<br>forks,not both|
|**[External Circuit]**|Existing models|Possible misinterpretation<br>Replaced bynewer syntax|
|**[Interconnect Model]**|Very flexible|Complicated<br>Difficult to check|
|**EMD**|Multi-die modules with<br>coupling|Complicated<br>Not referenced from IBS file (reversed reference)<br>Notyet fullysupported byall EDA tools|



* L and C values might be used in the EDA tool to create a transmission-line model or might be left as discrete L and C elements. The EDA tool might connect the discrete L and C elements in a series, T, or pi topology. The model changes the simulation results. The model creator should add a comment in the file to state the preferred modeling method. The model user might then select the appropriate model option in the EDA tool. 

## **Package model guidance** 

Package models should include all pins with coupling between signals, power, and ground. While it’s valid to use a package model that does not include the coupling between signals, power, and ground pins, a good quality model includes these coupling effects. Likewise, the loop inductance through the power and return paths could be modeled by a single inductance value in the power path, but such a model does not fully represent the voltage fluctuations used in the ISSO Pulldown effect. This topology is often for Touchstone (TS) file(s) for package models since the loop inductance is usually represented in only one value. 

IBIS Quality Specification Version 3.0 

Page 12 

A package model represented with a Touchstone S-parameter file must be passive and causal. Passivity and causality checks are slightly different between EDA tools. The model creator should include a comment telling which tool or threshold was used to check passivity and causality. 

Package models are often represented with SPICE subcircuits. The elements in the subcircuit should not be connected to a global reference node, known in SPICE as node 0, as noted on page 344 of the IBIS Specification version 7.2. A global reference node is not the same as the VSS terminal ([Pulldown Reference] or [Ground Clamp Reference]) in an IBIS model. Connections to a global reference node might make sense for controlled voltage sources used to mathematically reproduce frequency-domain data or if VSS is a defined path in the subcircuit and the model reference truly is the universe. 

## 3.1.4 {LEVEL 4} On-die and on-package decoupling included 

The inclusion of on-die and on-package decoupling can have a significant effect on the SSO calculation in the buffer model. On-die decoupling (non-ideal capacitance) is an important part of the component PDN. The on-die decoupling is probably included in an: 

- [Interconnect Model] section (IBIS-ISS or Touchstone models) 

- [External Circuit] and [Circuit Call] sections 

- [PDN Domain], Signal_name, Bus_label, [PDN Model], C_pdn, R_pdn, and R_leak. 

   - new keywords and parameters in 7.1 (BIRD198.3) 

The on-package decoupling is included in the package model. 

## 3.2 Component Pin Requirements 

Requirements for the [Pin] section: 

## 3.2.1 {LEVEL 2} [Pin] section complete 

All pins must be defined for a component. In addition to signal pins: 

- No Connect pins must be represented with model name NC. 

- Power pins must be represented with model name POWER. 

- Ground pins must be represented with model name GND. 

- The variety of [Model]s assigned to pins matches the variety of buffer characteristics described in the datasheet, and each pin has the correct [Model] or [Model Selector] assigned to it. 

- Special Pins (e.g., analog) are to be represented in the [Pin] section, even if they are marked NC. Explanatory comments are recommended for these. A common practice is to represent analog pins with Terminator models, so that waveforms of crosstalk received at the pins can be viewed in EDA tools. 

For IBIS buffer [Model] libraries, it is recommended that one pin be used for every model and that the pin name be the same as the model name. 

IBIS Quality Specification Version 3.0 

Page 13 

## 3.2.2 {LEVEL 3} [Pin] RLC values are present and reasonable 

For a LEVEL 2 model, pin model values are optional, but they are mandatory for a LEVEL 3 model (that is, a model suitable for timing). To pass this check the RLC values must be present for all signal pins in the [Pin] section, or [Package Model] must be present. Pin model values should either be measured or extracted using a 2D or 3D solver. Reasonable signal pin model values will result in impedance and delay characteristics that fall in the ranges: 

```
TD = SQRT(LC)   < 300 ps
Z0 = SQRT(L/C)  < 100 ohm
```

L and C values might be used in the EDA tool to create a transmission-line model or might be left as discrete L and C elements. The EDA tool might connect the discrete L and C elements in a series, T, or pi topology. The model changes the simulation results. The model creator should add a comment in the file to state the preferred modeling method. The model user might then select the appropriate model option in the EDA tool. 

Note that IQ check 3.1.2. also requires that each [Pin] RLC value falls within the min/max range as given by the [Package] keyword. The [Package] keyword can be adjusted to accommodate. 

## 3.3 Component Diff Pin Requirements 

Requirements for the optional [Diff Pin] section: 

## 3.3.1 {LEVEL 2} [Diff Pin] referenced pin models match 

It is expected that both pins of a differential pair will use the same [Model]. If the buffer models referenced by the two physical pins of a [Diff Pin] entry are not the same [Model] name, a comment or [Notes] entry must be present to explain why. 

## 3.3.2 {LEVEL 3} [Diff Pin] Vdiff and Tdelay_* complete and reasonable 

For input and I/O pins Vdiff must be defined, non-zero and positive. For output and I/O pins Tdelay_typ, Tdelay_min, and Tdelay_max data can be zero, but must be defined. Both Vdiff and Tdelay_* are measured relative to the die pads and must not include additional package delays and offsets. Output pins should have NA for Vdiff. For input pins Tdelay_typ, Tdelay_min, and Tdelay_max must be NA. 

## 3.4 Component Pin Mapping Requirements 

## 3.4.1 {LEVEL 4} [Pin Mapping] section is included for each component 

The [Pin Mapping] section must include all I/O pins from the [Pin] section. This requirement is checked by IBISCHK. The IBIS specification 7.0 states, “If the [Pin Mapping] keyword is present, then the bus 

IBIS Quality Specification Version 3.0 

Page 14 

connections for every pin listed under the [Pin] keyword whose model_name is not POWER, GND or NC shall be given.” 

## 3.4.2 {LEVEL 4} [Pin Mapping] table includes power and ground pins 

If [IBIS Ver] is less than 7.0, then all power pins must be included in [Pin Mapping] table. In Version 7.0 the requirement is relaxed (by BIRD182) to link [Pin Mapping] bus labels to [Pin] signal names. Additionally, the [Interconnect Model] and [EMD Model] syntax have rules to map power rails by keywords [Bus Label] and [Die Supply Pads]. Therefore, if [IBIS Ver] is 7.0 or greater, “If a pin has model 

name POWER or GND and there is no entry for this pin under the [Pin Mapping], [Bus Label], or 

[Die Supply Pads] keywords then the bus_label for that pin will be its signal name.” (IBIS Specification Version 7.2, pg 48) 

## 3.4.3 {LEVEL 4}   Specify [Merged Pins] keyword if applicable 

If the package model merges pins under the [Define Package Model] and [Model Data] keywords, then the [Merged Pins] keyword must be defined. 

## 4. [Model Selector] Section 

## 4.1 {LEVEL 2} [Model Selector] entries have reasonable descriptions 

Each line of the [Model Selector] keyword must have two fields. The first field lists the referenced [Model] name and second field contains a short description of the model shown in first field. The purpose of the description is to aid the user of the EDA tool in making intelligent buffer model selections. It can be used by the EDA tool in a user interface dialog box as the basis of an interactive buffer selection mechanism. An example of usage of [Model Selector] with an appropriate description might be a programmable buffer in DDR3, where the description may include the impedance of the driver and the applicable maximum frequency of the model (800 Mbps, 34-ohm Data I/O with no ODT). It is recommended to have a specific description in the [Notes] section about the existence of [Model Selector] in an IBIS file with a short explanation of why it was used, possibly with references to the data sheet for further explanation. 

## 4.2 {LEVEL 2} Default [Model Selector] entries are consistent 

The first entry under each [Model Selector] keyword is the default entry. They will be the models used by EDA tools if the user makes no specific choice. The set of default entries should be consistent, describing a state that may likely exist on the part, considering dependencies between them. For example, if the [Model Selector] entries describe controlled output impedances for a part on which all buffers are set to the same impedance, then the default entries for all [Model Selector] keywords would have the same impedance. There should not be one [Model Selector] defaulting to 35 ohms and another 

IBIS Quality Specification Version 3.0 

Page 15 

to 50 ohms in that case. Furthermore, the most frequently used setting of a [Model Selector] is the preferred default, if that can be determined. 

## 5. Model Section 

## 5.1 Model General Requirements 

## 5.1.1 {LEVEL 2} [Model] parameters have correct typ/min/max order 

For [Model] parameters, minimum corresponds to the conditions for weak/slow buffers, maximum corresponds to conditions for strong/fast buffers. These conditions are controlled by buffer selections for process, temperature and voltage conditions. 

Normally all keywords and subparameters scoped by the [Model] keyword with typ/min/max data have three columns corresponding to typical, weak/slow, and strong/fast, in order. The major exception is C_comp (including C_comp_*), which uses the numerically lowest value for minimum, and numerically highest for maximum. The highest [Temperature] value may fall into the minimum column or the maximum column, depending on technology. For CMOS technology the highest [Temperature] usually results in slow/weak operation and would appear in the minimum column. 

## 5.1.2 {LEVEL 2} [Model] C_comp is reasonable 

When present in the model as an alternative to the overall C_comp value, C_comp_pullup, C_comp_pulldown, C_comp_power_clamp, and C_comp_ground_clamp, or any combination thereof chosen to represent the die capacitance of the buffer, must sum to the original C_comp value. In other words, specifying the die capacitance in this more specific way should not change its overall value. 

Note that a model may contain a combination of C_comp_* parameters that appear inconsistent with the buffer type. For instance, an open-drain model might include the C_comp_pullup parameter. This is because a pullup structure, for instance, may exist in the silicon and simply not be used for a particular I/O type. However, its parasitic capacitance will still be present at the node. 

All general notes regarding choice of capacitance to report, given that die capacitance is frequency/voltage dependent, that apply to the C_comp parameter apply here as well. 

As is the case with C_comp, the C_comp_* parameters must be positive. Also, cases in which the total of the C_comp_* values is greater than 20 pF should be explained in the [Notes] section, as is suggested for C_comp. 

The values for C_comp must be checked for plausibility. Sometimes a compromise must be reached because C_comp in driving mode and C_comp in non-driving mode can be different. However, IBIS allows us to specify only a single value for total C_comp. 

The process of determining the appropriate C_comp depends on the type of systems in which the device is being used. For example, topology and data rate can affect the choice of C_comp. For low frequency point-to-point terminated systems, the effect of C_comp on signal integrity is typically less than high 

IBIS Quality Specification Version 3.0 

Page 16 

frequency systems with complex topologies. The model maker is encouraged to make necessary adjustments in C_comp that give the best correlation with SPICE simulation or with measurement data. 

One approach is to include both driving mode and non-driving mode C_comp values, with one commented out. An alternative is to calculate the average values. A suggested practice is to offer all of the above using comment lines to allow selection by the user: 

```
C_comp   3.0p 2.9p 3.1p    | C_comp_non-driving
|C_comp   4.0p 3.9p 4.1p   | C_comp_driving
|C_comp   3.5p 3.4p 3.6p   | (C_comp_non-driving + C_comp_driving) / 2
```

The set of values is not restricted to those shown above. C_comp might also be computed for other combinations of voltage and frequency. 

## 5.1.3 {LEVEL 2} [Temperature Range] is reasonable 

To pass this check the [Temperature Range] keyword must be present. The keyword needs some explanation because “minimum” corresponds to a slow, weak driver and “maximum” corresponds to a fast, strong driver. Slow and fast, in relation to temperature, depends on the process technology being described. 

Normally, CMOS has the relationship: 

```
Temp(minimum) > Temp(maximum)
```

While Bipolar normally has: 

```
Temp(minimum) < Temp(maximum)
```

Mixed and temperature-compensated technologies could go either way. 

The [Temperature Range] specified should normally match the temperatures at which the model was extracted. This is the chip die temperature, NOT the ambient temperature. The temperature being specified is usually higher than ambient temperature because the IC and parts around it in the measurement setup (or simulation) dissipate power. If the [Temperature Range] might not accurately represent chip die temperature, this should be documented in a comment. 

The reasons for differences between [Temperature Range] keyword and any model extraction temperature ranges should be documented as an exception, or comment. 

The [Temperature Range] should not exceed the safe operating temperature range as given on the data sheet. 

## 5.1.4 {LEVEL 2} [Voltage Range] or [* Reference] is reasonable 

[Voltage Range] is the operating supply voltage for a [Model]. It is required unless ALL FOUR of the other voltage reference keywords are supplied. When [Voltage Range] is used alone, the other keywords use default values. 

[Pullup Reference] defaults to [Voltage Range] 

IBIS Quality Specification Version 3.0 

Page 17 

[Pulldown Reference] defaults to 0 V 

[POWER Clamp Reference] defaults to [Voltage Range] 

[GND Clamp Reference] defaults to 0 V 

Regardless of whether [Voltage Range] or [* Reference] is used, the values must be reasonable and must represent the actual conditions of IBIS model extraction. The typical, minimum, and maximum values of the chosen voltages should normally follow the relationship: 

## minimum < typical < maximum 

The minimum and maximum voltages must fall within the maximum operating conditions specified by the data sheet but are not required to span the full range. Model users will be looking for minimum and maximum voltages that will reflect the range of supply voltages for their design, which will usually not stray more than 10% from the nominal voltage. If a buffer can be operated at more than one nominal voltage, a separate [Model] should be created for each nominal voltage, with reasonable minimum and maximum values for each typical voltage. In this case [Model Selector] would be used to allow the user to choose the nominal voltage used for the application. 

There should be consistency among models of the same nominal voltage. For example, all 2.5 V buffer models used for one [Component] would be expected to have the same minimum values and the same maximum values. Departures from this must be documented. 

## 5.2 Model Switching Behavior Requirements 

A few parameters in the [Model] and [Model Spec] sections specify the switching characteristics of input and I/O buffers, in response to waveforms. These values must be defined the same as in the component datasheet for timing calculations to be correct. 

## 5.2.1 {LEVEL 3} [Model] Vinl and Vinh reasonable 

The Vinl and Vinh parameters of the [Model] keyword represent the range of input threshold voltages for a population of buffers. The Vinl and Vinh parameters would correspond to the threshold values for Vinl and Vinh in a data sheet, in the case where only a single value applies for each, under all conditions. The [Model] Vinl and Vinh values must match corresponding values in [Model Spec], when [Model Spec] is present. The [Model] Vinl and Vinh values are normally worst case and may correspond to typical, minimum, or maximum values in the [Model Spec] keyword, as appropriate. 

For I/O buffers, Vinl and Vinh values should be below and above, respectively, Vmeas. Exceptions to this should be explained in a comment. 

## 5.2.2 {LEVEL 3} [Model Spec] Vinl and Vinh reasonable 

Because the input switching uncertainty region defined by the Vinl and Vinh sub-parameters of the [Model] section (See section 5.2.1.) can be affected by power supply fluctuation for many I/O standards, a range may be specified for these parameters in the [Model Spec] section. The “minimum” and “maximum” values given must be correct for the “minimum” and “maximum” values given for the 

IBIS Quality Specification Version 3.0 

Page 18 

supply voltage in the [Voltage Range] keyword. Vinl and Vinh are needed only for Input and I/O types of models. 

## 5.2.3 {LEVEL 3} [Model Spec] Vinl+/- and Vinh+/- complete and reasonable 

For input buffers with different voltage thresholds for rising and falling edges, Vinh+, Vinh-, Vinl+, and Vinl- are given in the [Model Spec] section. This would be required for inputs that exhibit hysteresis, such as Schmitt trigger devices. For I/O buffers, Vinl+ and Vinh- values should be below and above, respectively, Vmeas. Exceptions to this should be explained in a comment. 

## 5.2.4 {OPTIONAL} [Model Spec] Pulse subparameters complete 

Ordinarily when an input voltage level rises above Vinl or falls below Vinh, there is a possibility that the input will switch. If the data sheet specifies that input voltage levels can rise above Vinl or fall below Vinh for short periods of time with no possibility of being sensed as an input logic level change, then Pulse_high, Pulse_low, Pulse_time can be given in the [Model Spec] section. 

While all buffers exhibit this characteristic to some degree, the IBIS format may not be flexible enough to adequately represent the behavior. Therefore, a model for which this data is present in the data sheet might not have Pulse parameters in the IBIS file. 

## 5.2.5 {LEVEL 2} [Model Spec] S_Overshoot subparameters complete and match data sheet 

All input and I/O buffers should have S_overshoot_high and S_overshoot_low in the [Model Spec] section. The values must match the voltage limits beyond which the device may not function correctly. These limits may be different from the absolute maximum ratings, which may be related to device destruction. The functional limits may not be found in some data sheets. 

## 5.2.6 {LEVEL 2} [Model Spec] S_Overshoot subparameters track typ/min/max 

When overshoot voltage limits are different in minimum and maximum corners, S_overshoot_high and S_overshoot_low should track these differences. For example, S_overshoot_high may increase with the higher supply voltage assumed for maximum mode. 

## 5.2.7 {LEVEL 2} [Model Spec] D_Overshoot_* subparameters complete and match data sheet 

If greater levels of overshoot can be tolerated for short periods of time and is specified in the data sheet, these must be given as D_overshoot_high, D_overshoot_low, and D_overshoot_time subparameters of the [Model Spec] keyword. For some technologies the data sheet may specify different parameters to address this concept. For example, data sheets may specify dynamic allowances expressed as current limits that override voltage limits, or a time-voltage area limit may be specified instead of a simple time window. In this case the method by which D_overshoot_high, 

IBIS Quality Specification Version 3.0 

Page 19 

D_overshoot_low, and D_overshoot_time have been determined should be documented in the IBIS file as comments. 

## 5.2.8 {LEVEL 2} [Model Spec] D_Overshoot_* subparameters track typ/min/max 

When D_overshoot_* voltage limits are present and different in minimum and maximum corners, D_overshoot_high and D_overshoot_low should track supply voltage and process changes across the corners. For example, D_overshoot_high may increase with the higher supply voltage assumed for maximum mode. 

## 5.2.9 {LEVEL 3} [Receiver Thresholds] Vth present and matches data sheet, if needed 

If [Receiver Thresholds] are needed to represent input behavior, the Vth subparameter must be present if the signal is single-ended. Vth is the nominal input threshold voltage at voltage temperature and process conditions that define typical. Vth must match the input buffer timing measurement threshold in the data sheet. 

An example of a technology where [Receiver Thresholds] can be used is the DDR Memory Interface. In DDR, the input threshold voltage is nominally 0.50 * VDDQ. For DDR2, VDDQ is allowed to change from 1.7 to 1.9 V, nominally 1.8 V. In this case Vth would be specified as 0.9 V. IBIS tools will adjust the threshold voltage actually used as some system voltage fluctuates. 

## 5.2.10 {LEVEL 3} [Receiver Thresholds] Vth_min and Vth_max present and match data sheet, if needed 

Vth_min is the lowest actual input threshold voltage at typical supply voltage, process, and temperature conditions. Likewise, Vth_max is the highest actual input threshold voltage at typical supply voltage, process, and temperature conditions. These are often specified as tolerance values in data sheets, representing an uncertainty as to where Vth actually lies. Threshold changes due to minimum and maximum power supply variation are in addition to the Vth_min and Vth_max values. Vth_min and Vth_max must be present if the data sheet specifies a tolerance for Vth under typical conditions. 

For example, the input threshold voltage for DDR technology is allowed to range from 

0.49 * VDDQ to 0.51 * VDDQ, nominally 0.50 * VDDQ. For DDR2, VDDQ is allowed to change from 1.7 to 1.9 V, nominally 1.8 V. With the above definition of Vth, Vth_min and Vth_max, the values are calculated as follows: Vth = 0.9 V, Vth_min = 0.49 * 1.8 = 0.882 V and 

Vth_max = 0.51 * 1.8 = 0.918 V. As explained above, the variation in Vth only includes the effect of change of process and temperature at nominal voltage, which in this example is 1.8 V. 

## 5.2.11 {LEVEL 3} [Receiver Thresholds] Vinh_ac, Vinl_ac present and match data sheet, if needed 

IBIS Quality Specification Version 3.0 

Page 20 

Vinh_ac, Vinl_ac are the voltages above/below which the input signal must cross before the receiver can be guaranteed to change state. Vinh_ac, Vinl_ac overrides the Vinh and Vinl defined earlier in the [Model] or [Model Spec] section. 

The values given for Vinl_ac and Vinh_ac must match those in the data sheet. Note, however, that these parameters are required to be specified as offsets to Vth in the IBIS model, while they may be given as absolute voltages in the data sheet. Therefore, some conversion may be necessary. For instance, taking the SSTL18 standard as an example, the data sheet might call out 0.9 V for Vth and 1.150 V for Vinh_ac, which would require that Vinh_ac be given the value +250 mV in the IBIS file. 

## 5.2.12 {LEVEL 3} [Receiver Thresholds] Vinh_dc, Vinl_dc present and match data sheet, if needed 

Vinh_dc and Vinl_dc are DC input voltage thresholds which determine the boundary conditions under which the receiver will NOT change state. 

The values given for Vinl_dc and Vinh_dc must match those in the data sheet. Note, however, that these parameters are required to be specified as offsets to Vth in the IBIS model, while they may be given as absolute voltages in the data sheet. Therefore, some conversion may be necessary. For instance, taking the SSTL18 standard as an example, the data sheet might call out 0.9 V for Vth and 1.0 V for Vinh_dc, which would require that Vinh_dc be given the value +100 mV in the IBIS file. 

## 5.2.13 {LEVEL 3} [Receiver Thresholds] Tslew_ac/Tdiffslew_ac present and match 

## data sheet, if needed 

If the data sheet specifies a maximum time that an incoming signal may take to transition between Vinl_ac and Vinh_ac, then the [Receiver Thresholds] Tslew_ac parameter should be set to that value. For differential receivers the Tdiffslew_ac parameter should be set to the maximum allowable transition time between -Vdiff_ac and +Vdiff_ac. 

## 5.2.14 {LEVEL 3} [Receiver Thresholds] Threshold_sensitivity and Ext_ref present and match data sheet, if needed 

If the data sheet indicates that Vth is not a fixed value and depends on some reference voltage such as an external reference source or a supply voltage, then both Threshold_sensitivity and Reference_supply parameters must be present in [Receiver Thresholds]. For example, it is common for HSTL technology to require a Reference_supply value of “Ext_ref” and a Threshold_sensitivity value of “1”. 

## 5.3 Model I-V Table Requirements 

The term "table" as used in this document refers to rows and columns of numbers appearing in the text of the IBIS file. The term "curve" refers to the visual plotting of table data. Some checks are more easily performed visually. 

IBIS Quality Specification Version 3.0 

Page 21 

The voltage columns in the [Pullup] and [POWER Clamp] tables in IBIS files are Vcc-relative. This means that the voltage values in the first column are actually inverted offsets from Vcc. For example, the value at 0 V in a [Pullup] table is actually measured at Vcc and the value at Vcc in the table is measured at 0 V. Bear this in mind when checking Vcc-relative tables. The formula is: 

```
Vtable = Vcc - Voutput
```

Curve viewing tools may offer the ability to translate Vcc-relative tables so that the curves viewed are ground relative. 

## 5.3.1 {LEVEL 2} I-V tables have correct typ/min/max order 

Inspect every I-V table. Check for proper order of the I-V tables. The order of the column values in the table must be: 

voltage, typical current, minimum current, maximum current 

In most cases the maximum current should be greater than the typical current, which should be greater than the minimum current, in the active region (e.g., where device is not clamping). The most common exception is for compensated devices, where the typical, minimum, and maximum curves may nearly overlay each other. Also, [POWER Clamp] curves may exhibit crossovers due to differences in the voltages at which clamping begins. 

This check is easily accomplished by viewing the curves and checking visually. Checking combined curves is preferred, but checking of individual curves is acceptable. 

## 5.3.2 {LEVEL 2} [Pullup] voltage sweep range is correct 

The voltage column in the [Pullup] table should extend from -Vcc to +2 * Vcc, For the purpose of this check, Vcc is defined by the [Pullup Reference] keyword for this check, or [Voltage Range] if [Pullup Reference] is not present. 

## 5.3.3 {LEVEL 2} [Pulldown] voltage sweep range is correct 

The voltage column in the [Pulldown] table should extend from -Vcc to +2 * Vcc. For the purpose of this check, Vcc is defined by the [Pullup Reference] keyword for this check, or [Voltage Range] if [Pullup Reference] is not present. 

## 5.3.4 {LEVEL 2} [POWER Clamp] voltage sweep range is correct 

The voltage column in the [POWER Clamp] should extend at least from -Vcc to 0 (it is permitted and recommended to extend from –Vcc to +2 * Vcc, particularly where on-die termination is used). For the purpose of this check, Vcc is defined by the [POWER Clamp Reference] keyword for this check, or [Voltage Range] if [POWER Clamp Reference] is not present. 

IBIS Quality Specification Version 3.0 

Page 22 

## 5.3.5 {LEVEL 2} [GND Clamp] voltage sweep range is correct 

The voltage column in the [GND Clamp] should extend at least from -Vcc to +Vcc (it is permitted and recommended to extend from –Vcc to +2 * Vcc, particularly where on-die termination is used). For the purpose of this check, Vcc is defined by the [POWER Clamp Reference] keyword for this check, or [Voltage Range] if [POWER Clamp Reference] is not present. 

## 5.3.6 {LEVEL 2} I-V tables do not exhibit stair-stepping 

There should be no stair stepping of any I-V tables, with flat sections and abrupt jumps. This is caused by insufficient significant digits in the table current columns. This problem appears in early versions of the s2ibis2 program, originally from North Carolina State University (NCSU). Poor measurement resolution could also cause this effect. 

This check is easily accomplished by viewing the curves and checking visually. 

## 5.3.7 {LEVEL 2} Combined I-V tables are monotonic 

Check that the combined tables are monotonically increasing, i.e., there are no slope reversals in the current values. 

This check is easily accomplished by viewing the curves and checking visually. Alternatively, IBISCHK 4.2.1 or above will perform the same check automatically. 

Note that IBISCHK reports only the first non-monotonic points in each table. After fixing the data IBISCHK should be run again. 

## 5.3.8 {LEVEL 2} [Pulldown] I-V tables pass through zero/zero 

Typical, minimum, and maximum [Pulldown] table currents should all pass through approximately 0 mA at the 0 volt point in the voltage column, for full swing technologies such as CMOS. All three current columns should pass through zero current at the zero-volt line in the table, except in special cases (i.e., TTL, PECL, LVDS, or SERDES driver). 

## 5.3.9 {LEVEL 2} [Pullup] I-V tables pass through zero/zero 

Typical, minimum, and maximum [Pullup] table currents should all pass through approximately 0 mA at the 0 volt point in the voltage column, for full swing technologies such as CMOS. All three current columns should pass through zero current at the zero-volt line in the table, except in special cases (i.e., TTL, PECL, LVDS, or SERDES driver). 

## 5.3.10 {LEVEL 2} No leakage current in clamp I-V tables 

For models without on-die termination, review each clamp table. The expected currents should be less than 1 uA in the normal operating ranges (typically from 0 to Vcc range in the table). IBISCHK will print a 

IBIS Quality Specification Version 3.0 

Page 23 

warning for clamp tables in which currents are never below 1 uA. If a table is truncated, use the extrapolated values based on the last two points prior to extrapolation. Or use a viewer which can combine the two clamp tables into one. Exceptions can exist for older TTL technologies where several milliamps may be observed and for some ECL and other technologies with which can have internal resistors. Exceptions should be understood and documented. 

## 5.3.11 {LEVEL 2} I-V behavior not double-counted 

Verify that clamping currents are found only in the [GND Clamp] and [POWER Clamp] I-V tables. Verify that currents that should be found in the [Pullup] and [Pulldown] tables are not found in the [GND Clamp] and [POWER Clamp] I-V tables. Verify that there is no duplication of clamping currents between the [GND Clamp] and [POWER Clamp] tables. If the buffer has on-die termination, verify that termination current is not included in both the [GND Clamp] and [POWER Clamp] tables in such a manner as to cause double counting of the actual current when the clamps are extrapolated and combined. 

NOTE: NCSU s2ibis may not correctly model on-die termination. It places the full termination characteristic in both [POWER Clamp] and [GND Clamp] tables, effectively double counting the termination when these tables are combined by the simulator. 

## 5.3.12 {LEVEL 2} On-die termination modeling documented 

Any IBIS models with on-die termination should be labeled as such using comment lines. On die termination should be modeled in [POWER Clamp] and/or [GND Clamp] tables, and possibly using [Add Submodel] if the termination is active only in non-driving mode. Document the method used to embed the termination into the clamps. 

## 5.3.13 {LEVEL 2} ECL models I-V tables swept from -Vcc to +2 * Vcc. 

I-V tables in ECL models should be swept from -Vcc to +2 * Vcc, where Vcc for ECL is defined as the difference between the most positive supply voltage and the most negative. This is true even though the operating range is narrower. IBIS specifies a fixed 2 V range, but using the actual supply range is a better practice. 

## 5.3.14 {LEVEL 2} Point distributions in I-V tables should be sufficient 

We recommend a minimum of 10 data points at points of inflection in I-V tables to prevent interpolation issues in simulations. 

## 5.4 Model V-T Table Requirements 

## 5.4.1 {LEVEL 2} Output and I/O buffers have sufficient V-T tables 

IBIS Quality Specification Version 3.0 

Page 24 

Push-pull Output and I/O buffers should have two [Rising Waveform] and two [Falling Waveform] tables. Open-source and Open-drain buffers may have one [Rising Waveform] and one [Falling Waveform] table. If less than four V-T tables are present, then this should be explained in comments. 

The R_fixture value for V-T tables should be close to the characteristic impedance (Z0) of the transmission line for the application system at which the device is expected to operate. R_fixture for most legacy systems is close to 50 ohms: 

R_fixture connected to [Pullup Reference] 

Rising V-T Falling V-T R_fixture connected to = [Pulldown Reference] Rising V-T Falling V-T 

Differential and other terminated technologies may be modeled using two V-T tables by including a V_fixture at the common mode voltage, or close to the region of operation. For example: 

R_fixture to Vcm (Common Mode Voltage) Rising V-T Falling V-T 

For technologies such as LVDS which may not be compatible with the test fixture voltages required for [Ramp] data, at least two waveforms are required. 

## 5.4.2 {LEVEL 2} V-T tables have reasonable point distribution 

V-T tables should be well behaved, with continuous second derivative. V-T point density should be sufficient in areas with non-zero second derivative. For example, a low to high state transition should have at least 10 points. 

This check is easily accomplished by viewing the curves and checking visually. 

## 5.4.3 {LEVEL 3} V-T table duration is not excessive 

To avoid the "over clocking" issue, excess V-T points may be removed to match the V-T duration corresponding to the maximum data rate or frequency at which the device is expected to operate. When removing trailing V-T points the final DC value must be achieved, i.e., the ending slope should be very small. Since the two sets of V-T tables describe the relative on and off switching delay between the pullup and pulldown transistors, relative time position between all tables with the same edge direction and corner must be maintained when removing the leading excess V-T points. The number of excess V-T points removed can be different between corners (typical, minimum and maximum) but it is recommended to explain the difference as comments of the IBIS file. 

## 5.4.4 {LEVEL 2} V-T table endpoints match fixture voltages 

If the V_fixture values equal the supply reference voltages for the [Pullup] or [Pulldown] tables, then either the starting or ending points of the V-T tables are expected to equal these V_fixture values. This 

IBIS Quality Specification Version 3.0 

Page 25 

applies to full swing technologies such as CMOS, and not to technologies such as TTL, PECL, LVDS, or SERDES driver, which do not necessarily swing rail to rail. This check does not apply in cases where internal pullups/pulldowns or bias conditions exist such that the combined I-V tables have current flows at the V_fixture voltages. 

For example, for a 3.3 V device with the [Voltage Range] set to 3.3 V, V_fixture = 3.3 V, and R_fixture = 50 ohms, the [Rising Waveform] table should end at 3.3 V, and the [Falling Waveform] table should begin at 3.3 V. 

## 5.5 Model [Ramp] Data Requirements 

The [Ramp] section is required even if [Rising Waveform] and [Falling Waveform] are present in a [Model]. [Ramp] information is used in some tools for non-simulation purposes, for example quickly finding the fastest pin on a net. 

## 5.5.1 {LEVEL 2} [Ramp] R_load present if value other than 50 ohms 

If the [Ramp] data was measured using a load resistor other than 50 ohms, the [Ramp] section has an R_load subparameter giving the load resistor value used. 

## 5.5.2 {LEVEL 2} [Ramp] typ/min/max order is correct 

The typical, minimum, and maximum [Ramp] values are taken from typical, minimum, and maximum buffer measurements. They are not necessarily sorted by dV, dt, or dV/dt. Although the progression from minimum to maximum usually has dV increasing and dt decreasing, the correct order is actually determined by the test conditions used, the same conditions used to derive typ/min/max I-V tables. 

## 5.5.3 {LEVEL 2} [Ramp] dV value is consistent with I-V table calculations 

The [Ramp] dV values must match values calculated by applying the [Ramp] R_load and fixture voltage values to the I-V tables for typ/min/max conditions. The high and low state voltages are determined using the I-V table calculations, and 60% of the difference between these is compared to each [Ramp] dV value. The error must not exceed 5% of the dV calculated from the I-V tables. 

## 5.5.4 {LEVEL 2} [Ramp] dt is consistent with 20%-80% crossing time 

Each dt value matches within 10% the difference between the times of crossing the 20% voltage point and the 80% voltage point on the corresponding [Rising Waveform] or [Falling Waveform] with test fixture most similar to the [Ramp] test fixture, if matching V-T tables are present. 

This check is to be performed using V-T tables with V_fixture or R_fixture matching [Ramp] fixture values. The waveform R_fixture must match [Ramp] R_load, or 50 ohms if not specified. The [Rising Waveform] must have V_fixture equal to 0 V. The [Falling Waveform] must have V_fixture, V_fixture_min, and V_fixture_max values must correspond to the [Pullup Reference] or [Voltage Range] typical, minimum, and maximum values, respectively. Reasonably small values of C_fixture, L_fixture, 

IBIS Quality Specification Version 3.0 

Page 26 

R_dut, L_dut, and C_dut parameters in [Rising Waveform] and [Falling Waveform] can be overlooked in the V-T table selection process, although these may degrade the correlation of [Ramp] to V-T table endpoints. 

If suitable waveforms for this check are not present, an appropriate alternate reference for dt may be chosen. This may be simulated or measured waveforms, or a datasheet. 

## 5.6 Output Timing Checks 

## 5.6.1 {LEVEL 3} [Model Spec] Vmeas and Vref used if typ/min/max variation 

Usually, Vref and Vmeas have the same value for push-pull technologies and are specified to vary in proportion to supply voltage for typ/min/max conditions. Vmeas and Vref parameters in a [Model Spec] keyword would be used to convey any typ/min/max variation of these. 

## 5.6.2 {LEVEL 3} Vref consistent for Open-drain, Open-source, and ECL Model_types 

For Open-drain models [Model] or [Model Spec] Vref must be above Vmeas, and it is usually set to the [Pullup Reference] voltage. For Open-source and Open-sink models Vref must be below Vmeas, and it is usually set to the [Pulldown Reference] voltage, typically zero. For ECL models Vref must be below Vmeas and is usually 2 V below [Pullup Reference]. 

## 5.7 Model ISSO Table Requirements 

5.7.1 {LEVEL 4} All output-capable models include [ISSO PU] and [ISSO PD] tables The ISSO table data must correlate with the associated pullup and pulldown curves. IBISCHK7 checks the conditions: 

```
      Isso_pd(0) = Ipd(Vcc)
```

```
      Isso_pu(0) = Ipu(Vcc)
      Isso_pd(Vcc) = 0
      Isso_pu(Vcc) = 0
```

## 5.7.2 {LEVEL 4} ISSO tables have correct typ/min/max order 

Generally, the current values for each voltage point in the [ISSO PU] and [ISSO PD] tables should have the value in the minimum column less than the value in the typical column, which is less than the value in the maximum column. Viewed as a curve, these curves might cross each other for short ranges, but the order should apply generally; |Imin| < |Ityp| < |Imax|. 

IBIS Quality Specification Version 3.0 

Page 27 

## 5.7.3 {LEVEL 4} ISSO tables have sufficient point distribution 

We recommend a minimum of 10 data points at points of inflection in I-V tables to prevent interpolation issues in simulations. The table data viewed as a curve should not have sharp changes of the slope of the curve. See appendix A (Smoothness) for a possible checking algorithm. 

## 5.7.4 {LEVEL 4} ISSO tables voltage sweep range is correct 

The [ISSO PU] and [ISSO PD] tables should span voltage range +/- VCC. Ibischk7 checks the correlation of the current at Vtable = +VCC, so that point is required. On the negative voltage side, the modulation behavior might break down and show 0 amps before the table voltage reaches -VCC. In this situation, it seems sufficient for the table to include the voltages down to the point where the current reaches 0 amps, but IBIS Specification version 7.1, page 91 states, “Each of the tables are aligned with and span the typical -Vcc to Vcc voltages.” 

## 5.8 Model I-T Table Requirements 

## 5.8.1 {LEVEL 4} Each [Rising Waveform] and [Falling Waveform] table includes a [Composite Current] table 

The [Composite Current] table is subordinate to the V-T waveforms and represents important current sink behavior that is important for power-aware simulation. 

## 5.8.2 {LEVEL 4} [Composite Current] waveform data points cover the same time range as the corresponding V-T waveforms 

The first time point in a [Composite Current] table must be the same as the first time point in the parent waveform table. The last time point in a [Composite Current] table must be the same as the last time point in the parent waveform table. 

## 5.8.3 {LEVEL 4} [Composite Current] waveforms must be time-aligned with corresponding V-T waveforms 

Each time point in the [Composite Current] table shows the current associated with the same time point (actual or interpolated) in the associated rising or falling waveform table. An indication of this being correct is that the maximum current value in a column (typ, min, max) is at a time point near the middle of the transition (high to low or low to high) of the parent waveform table. 

## 5.8.4 {LEVEL 4} [Composite Current] includes pre-driver behavior 

This requirement applies when the pre-driver draws current from the Pullup Reference node, the same power supply as the main driver. In keeping with the check for time-correlated current and voltage, the 

IBIS Quality Specification Version 3.0 

Page 28 

rising and falling waveform tables might need to be delayed with some inactive section at the beginning to allow time in the [Composite Current] table to represent the activity of the pre-driver circuit. This requirement can be checked by looking for significant changes in the [Composite Current] curve before the associated voltage waveform shows its transition. 

## 5.8.5 {LEVEL 4} Start and end points [Composite Current] values correlate with pullup and pulldown tables 

Like the start and end voltage values that ibischk7 calculates for rising and falling waveforms, the calculated current values from the load-line evaluation should match the start and end current values of the [Composite Current] tables. 

The requirement might not apply in all models since the [Composite Current] is measured at the Pullup Reference node and the pullup and pulldown currents are measured at the signal pin. If the currents are not equal, the model should include a comment to explain why the model is still correct. Such a comment waives this requirement. 

## 5.8.6 {LEVEL 4} [Composite Current] data includes current from correct voltage rails 

When a buffer circuit has more than one voltage supply node connected to [Pullup Reference] or [Voltage Range], the multiple currents into the circuit must be added to produce the values in the [Composite Current] table. The [Composite Current] table values do not include current from the [POWER Clamp Reference] node when the [Pin Mapping] data specifies a different bus_label for the power-clamp reference bus. 

This requirement cannot be checked from the data in the IBIS file. The connections or assumptions of the data extraction should be documented in the file. 

## 5.8.7 {LEVEL 4} [Composite Current] curve is flat at start and end 

The start and end values of a [Composite Current] table might be non-zero, but the derivative of the curve should be 0. A non-zero derivative at the start or end of the curve indicates that some activity was not captured in the time range of the waveform. 

## 5.8.8 {LEVEL 4} [Composite Current] table values should start or end at 0 when V_fixture = 0 

If V_fixture = 0 in a [Falling Waveform] table, then the [Composite Current] table should end with a value of 0 amps. If V_fixture = 0 in a [Rising Waveform] table, then the [Composite Current] table should start with a value of 0 amps. Even very small current values can add up to an erroneous current flow in a multi-buffer simulation. 

IBIS Quality Specification Version 3.0 

Page 29 

## 6. Correlation 

IBIS quality correlation designator "S" specifies that the model developer has simulated a buffer using identical test loads in SPICE and in IBIS and compared the results. Likewise, the “M” designator specifies that IBIS simulations and bench measurements have been compared. The intention of correlation is to assess the degree to which the IBIS model data will result in simulations that match SPICE simulations and/or bench measurements. By careful attention to detail and understanding the behavior of the I/O circuit, it is possible to achieve extremely close correlation between SPICE and IBIS simulation results. Be aware that not all IBIS behavioral simulators are created equal; discrepancies may be an artifact of the behavioral simulator rather than the IBIS model extraction process. 

If the “M” or “S” correlation designators are used the methods employed and results must be thoroughly documented. If the documentation is external to the IBIS file, the IBIS file must contain comments sufficient to locate the correlation documentation. Inclusion of golden waveforms, either in external documents or in the IBIS file as [Test Data] and [Test Load] sections, or both, is recommended. 

For detailed information please refer to the "I/O Buffer Accuracy Handbook": 

https://www.ibis.org/accuracy/ 

The I/O Buffer Accuracy Handbook defines quantitative methods for correlating hardware measurements, SPICE simulations and IBIS simulations, and documenting the results of the correlation. It describes general principles such as overlay and envelope metrics, test circuits, and specific figures of merit to grade correlation results. Correlation methods are not limited to those described in the I/O Buffer Accuracy Handbook, but all methods used must be documented if the “M” and/or “S” designators are used. 

IBIS Quality Specification Version 3.0 

Page 30 

## Appendix A – Smoothness checking algorithm 

The smoothness of table data representing a curve can be tested algorithmically. The threshold on the smoothness metric might be adjusted with experience or to represent good, caution, or error conditions. The smoothness might be checked by various methods including visually, polynomial curve fitting, interpolation, etc. An example of a smoothness measure follows. 

1. Examine every 3 consecutive data points, f, g, and h, in the table. 

2. Calculate a line segment between end points f and h. 

3. Calculate the delta between the Y value of point g and the interpolated Y value at the same X value from the line segment in step 2. Smaller delta values are evidence of a smoother curve. 

4. Use the delta values to calculate an average error, or RSS error, or similar metric. The X delta value is also useful to weight the Y delta values. 

5. Compare the error metric to an empirically determined threshold to report a warning or error. h 

g 



f 

te 

IBIS Quality Specification Version 3.0 Page 31 

