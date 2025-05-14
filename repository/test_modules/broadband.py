import logging
from typing import List

from artiq.coredevice.ad9910 import AD9910
from artiq.coredevice.core import Core
from artiq.experiment import EnvExperiment
from artiq.experiment import delay
from artiq.experiment import kernel
from artiq.experiment import TFloat
# from ndscan.experiment import Fragment
# from ndscan.experiment.parameters import FloatParam
# from ndscan.experiment.parameters import FloatParamHandle
# from ndscan.experiment.parameters import IntParam
# from ndscan.experiment.parameters import IntParamHandle
#from pyaion.fragments.beam_setter import ControlBeamsWithoutCoolingAOM

# import repository.lib.constants as con
# from repository.lib.fragments.glitchfree_urukul_default_attenuation import (
#     GlitchFreeUrukulDefaultAttenuation,
# )
from repository.test_modules.ad9910_DRG import AD9910Ramper

# from repository.lib.fragments.suservo import LibSetSUServoStatic


logger = logging.getLogger(__name__)


class redBroadener(EnvExperiment):
    """
    Broadband red MOT
    """

    def build_fragment(self):
        self.setattr_device("core")
        self.core: Core

        # self.channelFoc = "urukul0_ch0"
        # # Urukul control base code
        # self.setattr_fragment(
        #     "injection_aom_ramper",
        #     AD9910Ramper,
        #     self.channelFoc,
        # )
        # self.injection_aom_ramper: AD9910Ramper

        # Raw AOM device - may be able to get rid?

        # self.setattr_fragment(
        #     "GlitchFreeUrukulDefaultAttenuation",
        #     GlitchFreeUrukulDefaultAttenuation,
        #     "urukul0_ch0",
        #     0.0,
        # )
        # self.GlitchFreeUrukulDefaultAttenuation: GlitchFreeUrukulDefaultAttenuation

        # %% DEVICES

        self.setattr_device("urukul0_ch0")
        self.urukul0_ch0: AD9910

        # %% PARAMETERS

        self.setattr_argument(
            "red_mot_static_freq",
            # FloatParam,
            "689 AOM static frequency",
            unit="MHz",
            # default=con.SFRMOT_FREQ,
        )
        # self.red_mot_static_freq: FloatParamHandle

        self.setattr_argument(
            "red_mot_static_amplitude",
            # FloatParam,
            description="689 AOM static amplitude",
            # default=con.SFRMOT_AMPLITUDE,
            min=0.0,
            max=1.0,
        )
        # self.red_mot_static_amplitude: FloatParamHandle

        self.setattr_argument(
            "red_mot_amplitude_dur_ramp",
            # FloatParam,
            description="689 AOM amplitude during ramp",
            default=1.0,
            min=0.0,
            max=1.0,
        )
        # self.red_mot_amplitude_dur_ramp: FloatParamHandle

        self.setattr_argument(
            "ramp_frequency",
            # FloatParam,
            "689 AOM ramp frequency",
            unit="kHz",
            # default=con.BBRMOT_RAMP_FREQ,
        )

        self.setattr_argument(
            "ramp_lower_frequency",
            # FloatParam,
            "Frequency of 689 AOM lowest point of ramp",
            unit="MHz",
            default=80e6,
        )
        self.setattr_argument(
            "ramp_upper_frequency",
            # FloatParam,
            "Frequency of 689 AOM highest point of ramp",
            unit="MHz",
            default=81e6,
        )
        self.setattr_argument(
            "ramp_type",
            # IntParam,
            "689 AOM ramp type (0=triangle,1=positive-saw,2=negative-saw)",
            default=1,
        )

        # self.ramp_frequency: FloatParamHandle
        # self.ramp_lower_frequency: FloatParamHandle
        # self.ramp_upper_frequency: FloatParamHandle
        # self.ramp_type: IntParamHandle

        # %% Kernel parameters

        # Initialised here so that it's available across kernels, but calculated
        # in device_setup in case it's varied in a scan
        self.ramp_rate = 0.0

        # self.debug_mode = logger.isEnabledFor(logging.DEBUG)

        # %% Kernel invariants
        # kernel_invariants = getattr(self, "kernel_invariants", set())
        # self.kernel_invariants = kernel_invariants | {
        #     "debug_mode",
        # }

    # def host_setup(self):
    #     super().host_setup()
    #     assert self.ramp_type.get() in [0, 1, 2], "Ramp type must be 0, 1 or 2"

    @kernel
    def device_setup(self):
        # self.device_setup_subfragments()

        # Precalculate the ramp rate required to get the requested modulation frequency
        self.ramp_rate = abs(
            (self.ramp_upper_frequency.get() - self.ramp_lower_frequency.get())
            * self.ramp_frequency.get()
        )

        if self.ramp_type.get() == 0:
            # Triangle waves will need to ramp twice as quickly
            self.ramp_rate *= 2

        # if self.debug_mode:
        #     logger.info(
        #         "Calculated required ramp_rate = %s kHz/s", self.ramp_rate * 1e-3
        #     )

        self.core.break_realtime()

        # Ensure the RF switch is on and the frequency is correct.
        # These are glitch free, so we do them each time
        # self.urukul0_ch0.set(con.SFRMOT_FREQ)
        self.urukul0_ch0.cfg_sw(True)
        self.urukul0_ch0.sw.on()

    # @kernel
    # def init(self):
    #     """
    #     Set up beam state for the red MOT, i.e. set up AOMs and close all shutters

    #     This is not in device_setup so that the user can choose when / whether to call it during each scan cycle
    #     """
    # Turn on all the AOMs but close all the shutters
    # self.all_beam_default_setter.turn_on_all(shutter_state=False)

    # Make sure that the shutters are closed before run_once starts
    # delay(self.all_beam_default_setter.get_max_shutter_delay())

    @kernel
    def turn_on_red_mot_aom(self):
        self.urukul0_ch0.init()
        self.urukul0_ch0.set_att(0.0)
        self.urukul0_ch0.set(
            frequency=self.red_mot_static_freq.get(),
            amplitude=self.red_mot_static_amplitude.get(),
        )
        self.urukul0_ch0.cfg_sw(True)  # trial
        delay(10e-9)
        self.urukul0_ch0.sw.on()

    @kernel
    def turn_off_red_mot_aom(self):

        self.urukul0_ch0.cfg_sw(False)
        delay(10e-9)
        self.urukul0_ch0.sw.off()  #

    @kernel
    def amplitude_update(self, amp):
        # self.urukul0_ch00.set_amplitude(amp) # didnt work
        self.urukul0_ch0.set(frequency=self.red_mot_static_freq.get(), amplitude=amp)

    @kernel
    def amp_freq_update(self, amp, freq):
        # self.urukul0_ch00.set_amplitude(amp) # didnt work
        self.urukul0_ch0.set(frequency=freq, amplitude=amp)

    @kernel
    def start_ramping_red(self):
        """
        Start modulation of the 689 DDS as configured
        """
        self.urukul0_ch0.set(
            frequency=self.red_mot_static_freq.get(),
            amplitude=self.red_mot_amplitude_dur_ramp.get(),
        )
        delay(10e-9)

        self.injection_aom_ramper.start_ramp(
            self.ramp_rate,
            self.ramp_lower_frequency.get(),
            self.ramp_upper_frequency.get(),
            self.ramp_type.get(),
        )

    @kernel
    def update_ramp(self, lower_freq, upper_freq, amp):
        """
        Update ramp modulation of the 689 DDS with specific values
        """
        # Calculate ramp rate
        ramp_rate = abs((upper_freq - lower_freq) * self.ramp_frequency.get())

        if self.ramp_type.get() == 0:
            # Triangle waves will need to ramp twice as quickly
            ramp_rate *= 2

        self.urukul0_ch0.set(frequency=(upper_freq + lower_freq) / 2, amplitude=amp)
        # self.urukul0_ch00.set(frequency = centre_freq, amplitude = amp)
        # delay(10e-9)
        self.injection_aom_ramper.start_ramp(
            ramp_rate, lower_freq, upper_freq, self.ramp_type.get()
        )

    @kernel
    def stop_ramping_red(self, freq=0.0):
        """
        Stop modulation of the 689 DDS and return to static (or specified) frequency
        """
        self.injection_aom_ramper.stop_ramp()

        if freq == 0.0:
            self.urukul0_ch0.set(
                frequency=self.red_mot_static_freq.get(),
                amplitude=self.red_mot_static_amplitude.get(),
            )
        else:
            self.urukul0_ch0.set(
                frequency=freq, amplitude=self.red_mot_static_amplitude.get()
            )

    # @kernel
    # def set_mot_detuning(self, detuning: TFloat):
    #     """Set the detuning of the MOT beams from the static frequency

    #     Does not affect ramp settings and so will have no effect if ramping is
    #     enabled.

    #     This method advances the timeline by the duration of an AD9910 SPI
    #     transaction.

    #     Args:
    #         detuning (float): Detuning in Hz
    #     """
    #     freq = (
    #         constants.RED_INJECTION_AOM_FREQUENCY
    #         + self.urukul0_ch0_static_detuning.get()
    #         + detuning
    #     )

    #     if self.debug_mode:
    #         logger.info(
    #             "Setting AOM detuning to %.3f kHz = %.6f MHz on %s",
    #             detuning * 1e-3,
    #             freq * 1e-6,
    #             self.urukul0_ch0,
    #         )

    #     self.urukul0_ch0.set(freq)

    # @kernel
    # def set_mot_suservo_amplitude(self, amplitude_multiple: TFloat):
    #     """
    #     Set the SUServo target amplitudes of all MOT beams

    #     Args:
    #         amplitude_multiple (TFloat): Amplitude of MOT beams, expressed as a multiple of the nominal amplitude
    #     """

    #     for i in range(len(self.suservo_fragments)):

    #         suservo_frag = self.suservo_fragments[i]
    #         nominal_setpoint = self.suservo_nominal_amplitudes[i]
    #         photodiode_offset = self.suservo_setpoint_offsets[i]

    #         setpoint = nominal_setpoint * amplitude_multiple + photodiode_offset

    #         if self.debug_mode:
    #             logger.info(
    #                 "Setting %s setpoint to %.2f x %.2f + %.4f = %.3f V",
    #                 suservo_frag,
    #                 amplitude_multiple,
    #                 nominal_setpoint,
    #                 photodiode_offset,
    #                 setpoint,
    #             )

    #         suservo_frag.set_setpoint(setpoint)
