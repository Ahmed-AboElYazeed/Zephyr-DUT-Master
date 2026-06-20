/*
 * Sponsored License - for use in support of a program or activity
 * sponsored by MathWorks.  Not for government, commercial or other
 * non-sponsored organizational use.
 *
 * File: dc_motor_math.h
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

#ifndef dc_motor_math_h_
#define dc_motor_math_h_
#ifndef dc_motor_math_COMMON_INCLUDES_
#define dc_motor_math_COMMON_INCLUDES_
#include "rtwtypes.h"
#include "rtw_continuous.h"
#include "rtw_solver.h"
#include "math.h"
#endif                                 /* dc_motor_math_COMMON_INCLUDES_ */

#include "dc_motor_math_types.h"
#include <string.h>

/* Macros for accessing real-time model data structure */
#ifndef rtmGetErrorStatus
#define rtmGetErrorStatus(rtm)         ((rtm)->errorStatus)
#endif

#ifndef rtmSetErrorStatus
#define rtmSetErrorStatus(rtm, val)    ((rtm)->errorStatus = (val))
#endif

#ifndef rtmGetStopRequested
#define rtmGetStopRequested(rtm)       ((rtm)->Timing.stopRequestedFlag)
#endif

#ifndef rtmSetStopRequested
#define rtmSetStopRequested(rtm, val)  ((rtm)->Timing.stopRequestedFlag = (val))
#endif

#ifndef rtmGetStopRequestedPtr
#define rtmGetStopRequestedPtr(rtm)    (&((rtm)->Timing.stopRequestedFlag))
#endif

#ifndef rtmGetT
#define rtmGetT(rtm)                   (rtmGetTPtr((rtm))[0])
#endif

#ifndef rtmGetTPtr
#define rtmGetTPtr(rtm)                ((rtm)->Timing.t)
#endif

#ifndef rtmGetTStart
#define rtmGetTStart(rtm)              ((rtm)->Timing.tStart)
#endif

/* Block signals (default storage) */
typedef struct {
  real_T Inductance;                   /* '<Root>/Inductance' */
  real_T Inertia;                      /* '<Root>/Inertia' */
} B_dc_motor_math_T;

/* Continuous states (default storage) */
typedef struct {
  real_T Integrator1_CSTATE;           /* '<Root>/Integrator1' */
  real_T Integrator_CSTATE;            /* '<Root>/Integrator' */
} X_dc_motor_math_T;

/* State derivatives (default storage) */
typedef struct {
  real_T Integrator1_CSTATE;           /* '<Root>/Integrator1' */
  real_T Integrator_CSTATE;            /* '<Root>/Integrator' */
} XDot_dc_motor_math_T;

/* State disabled  */
typedef struct {
  boolean_T Integrator1_CSTATE;        /* '<Root>/Integrator1' */
  boolean_T Integrator_CSTATE;         /* '<Root>/Integrator' */
} XDis_dc_motor_math_T;

#ifndef ODE3_INTG
#define ODE3_INTG

/* ODE3 Integration Data */
typedef struct {
  real_T *y;                           /* output */
  real_T *f[3];                        /* derivatives */
} ODE3_IntgData;

#endif

/* External inputs (root inport signals with default storage) */
typedef struct {
  real_T voltage_in;                   /* '<Root>/voltage_in' */
  real_T load_in;                      /* '<Root>/load_in' */
} ExtU_dc_motor_math_T;

/* External outputs (root outports fed by signals with default storage) */
typedef struct {
  real_T speed_sig;                    /* '<Root>/speed_sig' */
  real_T current_sig;                  /* '<Root>/current_sig' */
} ExtY_dc_motor_math_T;

/* Real-time Model Data Structure */
struct tag_RTM_dc_motor_math_T {
  const char_T *errorStatus;
  RTWSolverInfo solverInfo;
  X_dc_motor_math_T *contStates;
  int_T *periodicContStateIndices;
  real_T *periodicContStateRanges;
  real_T *derivs;
  XDis_dc_motor_math_T *contStateDisabled;
  boolean_T zCCacheNeedsReset;
  boolean_T derivCacheNeedsReset;
  boolean_T CTOutputIncnstWithState;
  real_T odeY[2];
  real_T odeF[3][2];
  ODE3_IntgData intgData;

  /*
   * Sizes:
   * The following substructure contains sizes information
   * for many of the model attributes such as inputs, outputs,
   * dwork, sample times, etc.
   */
  struct {
    int_T numContStates;
    int_T numPeriodicContStates;
    int_T numSampTimes;
  } Sizes;

  /*
   * Timing:
   * The following substructure contains information regarding
   * the timing information for the model.
   */
  struct {
    uint32_T clockTick0;
    time_T stepSize0;
    time_T tStart;
    SimTimeStep simTimeStep;
    boolean_T stopRequestedFlag;
    time_T *t;
    time_T tArray[1];
  } Timing;
};

/* Block signals (default storage) */
extern B_dc_motor_math_T dc_motor_math_B;

/* Continuous states (default storage) */
extern X_dc_motor_math_T dc_motor_math_X;

/* Disabled states (default storage) */
extern XDis_dc_motor_math_T dc_motor_math_XDis;

/* External inputs (root inport signals with default storage) */
extern ExtU_dc_motor_math_T dc_motor_math_U;

/* External outputs (root outports fed by signals with default storage) */
extern ExtY_dc_motor_math_T dc_motor_math_Y;

/* Model entry point functions */
extern void dc_motor_math_initialize(void);
extern void dc_motor_math_step(void);
extern void dc_motor_math_terminate(void);

/* Exported data declaration */

// Changed by AboElyazeed: from "const volatile real_T" to modify them in other file 

/* ConstVolatile memory section */
/* Declaration for custom storage class: ConstVolatile */
extern real_T dc_motor_math_Integrator1_IC;/* Referenced by: '<Root>/Integrator1' */
extern real_T dc_motor_math_Integrator_IC;/* Referenced by: '<Root>/Integrator' */
extern real_T dc_motor_math_J;/* Referenced by: '<Root>/Inertia' */
extern real_T dc_motor_math_K;/* Referenced by:
                                              * '<Root>/Ke'
                                              * '<Root>/Kt'
                                              */
extern real_T dc_motor_math_L;/* Referenced by: '<Root>/Inductance' */
extern real_T dc_motor_math_R;/* Referenced by: '<Root>/Resistance' */
extern real_T dc_motor_math_b;/* Referenced by: '<Root>/Damping' */

/* Real-time Model object */
extern RT_MODEL_dc_motor_math_T *const dc_motor_math_M;

/*-
 * The generated code includes comments that allow you to trace directly
 * back to the appropriate location in the model.  The basic format
 * is <system>/block_name, where system is the system number (uniquely
 * assigned by Simulink) and block_name is the name of the block.
 *
 * Use the MATLAB hilite_system command to trace the generated code back
 * to the model.  For example,
 *
 * hilite_system('<S3>')    - opens system 3
 * hilite_system('<S3>/Kp') - opens and selects block Kp which resides in S3
 *
 * Here is the system hierarchy for this model
 *
 * '<Root>' : 'dc_motor_math'
 */
#endif                                 /* dc_motor_math_h_ */

/*
 * File trailer for generated code.
 *
 * [EOF]
 */
