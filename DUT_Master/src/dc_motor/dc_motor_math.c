/*
 * Sponsored License - for use in support of a program or activity
 * sponsored by MathWorks.  Not for government, commercial or other
 * non-sponsored organizational use.
 *
 * File: dc_motor_math.c
 *
 * Code generated for Simulink model 'dc_motor_math'.
 *
 * Model version                  : 1.9
 * Simulink Coder version         : 25.1 (R2025a) 21-Nov-2024
 * C/C++ source code generated on : Mon Jun 15 02:55:26 2026
 *
 * Target selection: ert.tlc
 * Embedded hardware selection: ARM Compatible->ARM Cortex-M
 * Code generation objectives: Unspecified
 * Validation result: Not run
 */

#include "dc_motor_math.h"
#include "rtwtypes.h"
#include "dc_motor_math_private.h"

/* Exported data definition */

// Commented by AboElyazeed: to change them in other file 

// /* ConstVolatile memory section */
// /* Definition for custom storage class: ConstVolatile */
// const volatile real_T dc_motor_math_Integrator1_IC = 0.0;/* Referenced by: '<Root>/Integrator1' */
// const volatile real_T dc_motor_math_Integrator_IC = 0.0;/* Referenced by: '<Root>/Integrator' */
// const volatile real_T dc_motor_math_J = 0.01;/* Referenced by: '<Root>/Inertia' */
// const volatile real_T dc_motor_math_K = 0.01;/* Referenced by:
//                                               * '<Root>/Ke'
//                                               * '<Root>/Kt'
//                                               */
// const volatile real_T dc_motor_math_L = 0.5;/* Referenced by: '<Root>/Inductance' */
// const volatile real_T dc_motor_math_R = 1.0;/* Referenced by: '<Root>/Resistance' */
// const volatile real_T dc_motor_math_b = 0.1;/* Referenced by: '<Root>/Damping' */

/* Block signals (default storage) */
B_dc_motor_math_T dc_motor_math_B;

/* Continuous states */
X_dc_motor_math_T dc_motor_math_X;

/* Disabled State Vector */
XDis_dc_motor_math_T dc_motor_math_XDis;

/* External inputs (root inport signals with default storage) */
ExtU_dc_motor_math_T dc_motor_math_U;

/* External outputs (root outports fed by signals with default storage) */
ExtY_dc_motor_math_T dc_motor_math_Y;

/* Real-time model */
static RT_MODEL_dc_motor_math_T dc_motor_math_M_;
RT_MODEL_dc_motor_math_T *const dc_motor_math_M = &dc_motor_math_M_;

/*
 * This function updates continuous states using the ODE3 fixed-step
 * solver algorithm
 */
static void rt_ertODEUpdateContinuousStates(RTWSolverInfo *si )
{
  /* Solver Matrices */
  static const real_T rt_ODE3_A[3] = {
    1.0/2.0, 3.0/4.0, 1.0
  };

  static const real_T rt_ODE3_B[3][3] = {
    { 1.0/2.0, 0.0, 0.0 },

    { 0.0, 3.0/4.0, 0.0 },

    { 2.0/9.0, 1.0/3.0, 4.0/9.0 }
  };

  time_T t = rtsiGetT(si);
  time_T tnew = rtsiGetSolverStopTime(si);
  time_T h = rtsiGetStepSize(si);
  real_T *x = rtsiGetContStates(si);
  ODE3_IntgData *id = (ODE3_IntgData *)rtsiGetSolverData(si);
  real_T *y = id->y;
  real_T *f0 = id->f[0];
  real_T *f1 = id->f[1];
  real_T *f2 = id->f[2];
  real_T hB[3];
  int_T i;
  int_T nXc = 2;
  rtsiSetSimTimeStep(si,MINOR_TIME_STEP);

  /* Save the state values at time t in y, we'll use x as ynew. */
  (void) memcpy(y, x,
                (uint_T)nXc*sizeof(real_T));

  /* Assumes that rtsiSetT and ModelOutputs are up-to-date */
  /* f0 = f(t,y) */
  rtsiSetdX(si, f0);
  dc_motor_math_derivatives();

  /* f(:,2) = feval(odefile, t + hA(1), y + f*hB(:,1), args(:)(*)); */
  hB[0] = h * rt_ODE3_B[0][0];
  for (i = 0; i < nXc; i++) {
    x[i] = y[i] + (f0[i]*hB[0]);
  }

  rtsiSetT(si, t + h*rt_ODE3_A[0]);
  rtsiSetdX(si, f1);
  dc_motor_math_step();
  dc_motor_math_derivatives();

  /* f(:,3) = feval(odefile, t + hA(2), y + f*hB(:,2), args(:)(*)); */
  for (i = 0; i <= 1; i++) {
    hB[i] = h * rt_ODE3_B[1][i];
  }

  for (i = 0; i < nXc; i++) {
    x[i] = y[i] + (f0[i]*hB[0] + f1[i]*hB[1]);
  }

  rtsiSetT(si, t + h*rt_ODE3_A[1]);
  rtsiSetdX(si, f2);
  dc_motor_math_step();
  dc_motor_math_derivatives();

  /* tnew = t + hA(3);
     ynew = y + f*hB(:,3); */
  for (i = 0; i <= 2; i++) {
    hB[i] = h * rt_ODE3_B[2][i];
  }

  for (i = 0; i < nXc; i++) {
    x[i] = y[i] + (f0[i]*hB[0] + f1[i]*hB[1] + f2[i]*hB[2]);
  }

  rtsiSetT(si, tnew);
  rtsiSetSimTimeStep(si,MAJOR_TIME_STEP);
}

/* Model step function */
void dc_motor_math_step(void)
{
  if (rtmIsMajorTimeStep(dc_motor_math_M)) {
    /* set solver stop time */
    rtsiSetSolverStopTime(&dc_motor_math_M->solverInfo,
                          ((dc_motor_math_M->Timing.clockTick0+1)*
      dc_motor_math_M->Timing.stepSize0));
  }                                    /* end MajorTimeStep */

  /* Update absolute time of base rate at minor time step */
  if (rtmIsMinorTimeStep(dc_motor_math_M)) {
    dc_motor_math_M->Timing.t[0] = rtsiGetT(&dc_motor_math_M->solverInfo);
  }

  /* Outport: '<Root>/speed_sig' incorporates:
   *  Integrator: '<Root>/Integrator1'
   */
  dc_motor_math_Y.speed_sig = dc_motor_math_X.Integrator1_CSTATE;

  /* Sum: '<Root>/Add' incorporates:
   *  Gain: '<Root>/Ke'
   *  Gain: '<Root>/Resistance'
   *  Inport: '<Root>/voltage_in'
   *  Integrator: '<Root>/Integrator'
   *  Integrator: '<Root>/Integrator1'
   */
  dc_motor_math_Y.current_sig = (dc_motor_math_U.voltage_in - dc_motor_math_R *
    dc_motor_math_X.Integrator_CSTATE) - dc_motor_math_K *
    dc_motor_math_X.Integrator1_CSTATE;

  /* Gain: '<Root>/Inductance' */
  dc_motor_math_B.Inductance = 1.0 / dc_motor_math_L *
    dc_motor_math_Y.current_sig;

  /* Gain: '<Root>/Inertia' incorporates:
   *  Gain: '<Root>/Damping'
   *  Gain: '<Root>/Kt'
   *  Inport: '<Root>/load_in'
   *  Integrator: '<Root>/Integrator'
   *  Integrator: '<Root>/Integrator1'
   *  Sum: '<Root>/Add1'
   *  Sum: '<Root>/Subtract'
   */
  dc_motor_math_B.Inertia = ((dc_motor_math_K *
    dc_motor_math_X.Integrator_CSTATE - dc_motor_math_U.load_in) -
    dc_motor_math_b * dc_motor_math_X.Integrator1_CSTATE) * (1.0 /
    dc_motor_math_J);
  if (rtmIsMajorTimeStep(dc_motor_math_M)) {
    rt_ertODEUpdateContinuousStates(&dc_motor_math_M->solverInfo);

    /* Update absolute time for base rate */
    /* The "clockTick0" counts the number of times the code of this task has
     * been executed. The absolute time is the multiplication of "clockTick0"
     * and "Timing.stepSize0". Size of "clockTick0" ensures timer will not
     * overflow during the application lifespan selected.
     */
    ++dc_motor_math_M->Timing.clockTick0;
    dc_motor_math_M->Timing.t[0] = rtsiGetSolverStopTime
      (&dc_motor_math_M->solverInfo);
  }                                    /* end MajorTimeStep */
}

/* Derivatives for root system: '<Root>' */
void dc_motor_math_derivatives(void)
{
  XDot_dc_motor_math_T *_rtXdot;
  _rtXdot = ((XDot_dc_motor_math_T *) dc_motor_math_M->derivs);

  /* Derivatives for Integrator: '<Root>/Integrator1' */
  _rtXdot->Integrator1_CSTATE = dc_motor_math_B.Inertia;

  /* Derivatives for Integrator: '<Root>/Integrator' */
  _rtXdot->Integrator_CSTATE = dc_motor_math_B.Inductance;
}

/* Model initialize function */
void dc_motor_math_initialize(void)
{
  /* Registration code */
  {
    /* Setup solver object */
    rtsiSetSimTimeStepPtr(&dc_motor_math_M->solverInfo,
                          &dc_motor_math_M->Timing.simTimeStep);
    rtsiSetTPtr(&dc_motor_math_M->solverInfo, &rtmGetTPtr(dc_motor_math_M));
    rtsiSetStepSizePtr(&dc_motor_math_M->solverInfo,
                       &dc_motor_math_M->Timing.stepSize0);
    rtsiSetdXPtr(&dc_motor_math_M->solverInfo, &dc_motor_math_M->derivs);
    rtsiSetContStatesPtr(&dc_motor_math_M->solverInfo, (real_T **)
                         &dc_motor_math_M->contStates);
    rtsiSetNumContStatesPtr(&dc_motor_math_M->solverInfo,
      &dc_motor_math_M->Sizes.numContStates);
    rtsiSetNumPeriodicContStatesPtr(&dc_motor_math_M->solverInfo,
      &dc_motor_math_M->Sizes.numPeriodicContStates);
    rtsiSetPeriodicContStateIndicesPtr(&dc_motor_math_M->solverInfo,
      &dc_motor_math_M->periodicContStateIndices);
    rtsiSetPeriodicContStateRangesPtr(&dc_motor_math_M->solverInfo,
      &dc_motor_math_M->periodicContStateRanges);
    rtsiSetContStateDisabledPtr(&dc_motor_math_M->solverInfo, (boolean_T**)
      &dc_motor_math_M->contStateDisabled);
    rtsiSetErrorStatusPtr(&dc_motor_math_M->solverInfo, (&rtmGetErrorStatus
      (dc_motor_math_M)));
    rtsiSetRTModelPtr(&dc_motor_math_M->solverInfo, dc_motor_math_M);
  }

  rtsiSetSimTimeStep(&dc_motor_math_M->solverInfo, MAJOR_TIME_STEP);
  rtsiSetIsMinorTimeStepWithModeChange(&dc_motor_math_M->solverInfo, false);
  rtsiSetIsContModeFrozen(&dc_motor_math_M->solverInfo, false);
  dc_motor_math_M->intgData.y = dc_motor_math_M->odeY;
  dc_motor_math_M->intgData.f[0] = dc_motor_math_M->odeF[0];
  dc_motor_math_M->intgData.f[1] = dc_motor_math_M->odeF[1];
  dc_motor_math_M->intgData.f[2] = dc_motor_math_M->odeF[2];
  dc_motor_math_M->contStates = ((X_dc_motor_math_T *) &dc_motor_math_X);
  dc_motor_math_M->contStateDisabled = ((XDis_dc_motor_math_T *)
    &dc_motor_math_XDis);
  dc_motor_math_M->Timing.tStart = (0.0);
  rtsiSetSolverData(&dc_motor_math_M->solverInfo, (void *)
                    &dc_motor_math_M->intgData);
  rtsiSetSolverName(&dc_motor_math_M->solverInfo,"ode3");
  rtmSetTPtr(dc_motor_math_M, &dc_motor_math_M->Timing.tArray[0]);
  dc_motor_math_M->Timing.stepSize0 = 0.2;

  /* InitializeConditions for Integrator: '<Root>/Integrator1' */
  dc_motor_math_X.Integrator1_CSTATE = dc_motor_math_Integrator1_IC;

  /* InitializeConditions for Integrator: '<Root>/Integrator' */
  dc_motor_math_X.Integrator_CSTATE = dc_motor_math_Integrator_IC;
}

/* Model terminate function */
void dc_motor_math_terminate(void)
{
  /* (no terminate code required) */
}

/*
 * File trailer for generated code.
 *
 * [EOF]
 */
