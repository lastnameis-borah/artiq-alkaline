from artiq.experiment import *
from artiq.coredevice.core import Core
from artiq.coredevice.ad9910 import AD9910
from artiq.coredevice.ad9910 import _AD9910_REG_CFR2
from artiq.coredevice.ad9910 import _AD9910_REG_RAMP_LIMIT
from artiq.coredevice.ad9910 import _AD9910_REG_RAMP_RATE
from artiq.coredevice.ad9910 import _AD9910_REG_RAMP_STEP
from artiq.coredevice.urukul import CPLD
from artiq.coredevice.urukul import urukul_sta_pll_lock
from artiq.experiment import EnvExperiment
from artiq.experiment import kernel
from artiq.experiment import TFloat
from artiq.experiment import TInt32, TInt64
from artiq.experiment import delay

from numpy import ceil
from numpy import int32, int64


class redMOT(EnvExperiment):

    def build(self):
        self.setattr_device("core")
        self.core: Core
        self.setattr_device("urukul0_ch0")
        self.urukul0_ch0: AD9910

        self.setattr_argument("red_mot_static_freq", NumberValue(0.0, unit="MHz"))
        self.setattr_argument("red_mot_static_amplitude", NumberValue(0.0))
        self.setattr_argument("red_mot_amplitude_dur_ramp", NumberValue(0.0, unit="s"))
        self.setattr_argument("ramp_frequency", NumberValue(0.0, unit="Hz"))
        self.setattr_argument("ramp_lower_frequency", NumberValue(0.0, unit="MHz"))
        self.setattr_argument("ramp_upper_frequency", NumberValue(0.0, unit="MHz"))
        self.setattr_argument("ramp_type", NumberValue(0))


    def run(self):
        self.core.reset()
        # Precalculate the ramp rate required to get the requested modulation frequency
        self.ramp_rate = abs(
            (self.ramp_upper_frequency - self.ramp_lower_frequency)
            * self.ramp_frequency
        )
        print("Ramp rate: ", self.ramp_rate)

        if self.ramp_type == 0:
            # Triangle waves will need to ramp twice as quickly
            self.ramp_rate *= 2

        self.core.break_realtime()
        self.urukul0_ch0.cfg_sw(True)
        self.urukul0_ch0.sw.on()

    
    # def turn_on_red_mot_aom(self):
        self.urukul0_ch0.init()
        self.urukul0_ch0.set_att(0.0)
        self.urukul0_ch0.set(
            frequency=self.red_mot_static_freq,
            amplitude=self.red_mot_static_amplitude,
        )
        self.urukul0_ch0.cfg_sw(True)  # trial
        delay(10e-9)
        # self.urukul0_ch0.sw.on()

        """
        Start modulation of the 689 DDS as configured
        """
        self.urukul0_ch0.set(
            frequency=self.red_mot_static_freq,
            amplitude=self.red_mot_amplitude_dur_ramp,
        )
        delay(10e-9)

        self.injection_aom_ramper.start_ramp(
            self.ramp_rate,
            self.ramp_lower_frequency.get(),
            self.ramp_upper_frequency.get(),
            self.ramp_type.get(),
        )