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


class ad9910_DRGSweep(EnvExperiment):
    """
    This demonstrates the use of the AD9910's Digital Ramp Generator (DRG)
    """
    def build(self):
        self.setattr_device("core")
        self.dds:AD9910=self.get_device("urukul0_ch0")

    @kernel
    def run(self):
        self.core.reset()
        self.core.break_realtime()
        self.dds.cpld.init()
        self.dds.init()
        self.dds.sw.on()

        self.dds.set_att(0.0)
        # self.dds.set_amplitude(1.0)
        # self.dds.set_frequency(80e6)
        
        
        # self.dds.set(frequency=83 * MHz, amplitude=1.0)

        # --------------------------------------------------
        # Sweep from 80 MHz to 81 MHz, modulation rate = 25 kHz
        # --------------------------------------------------

        # # Compute FTW bounds from frequency (in Hz)
        # ftw_start = self.dds.frequency_to_ftw(80e6)  # ~0x147AE147
        # ftw_stop  = self.dds.frequency_to_ftw(81e6)  # ~0x14C290E3

        # # Step size and step rate (25 kHz cycle = 20 μs up + 20 μs down)
        # num_steps = 100
        # ftw_step = (ftw_stop - ftw_start) // num_steps  # ~45640
        # step_rate_cycles = 5  # SYSCLK cycles between steps (5 @ 1 GHz = 200 ns)

        # # Set ramp limits
        # self.dds.write64(0x0b, ftw_stop, ftw_start)  # RAMP_LIMIT register

        # # Set step size (same up and down)
        # self.dds.write64(0x0c, ftw_step, ftw_step)  # RAMP_STEP register

        # # Set ramp rate
        # self.dds.write32(0x0d, (step_rate_cycles << 16) | step_rate_cycles)  # RAMP_RATE

        # # Configure CFR2: DRG destination = FTW, DRG enabled
        # self.dds.set_cfr2(drg_destination=0,  # frequency
        #                     drg_enable=1,
        #                     drg_nodwell_high=0,
        #                     drg_nodwell_low=0)

        # # Enable bidirectional ramp mode in CFR1 (bit 15 = DRG_LOAD_LRR)
        # self.dds.set_cfr1(drg_load_lrr=1)

        # # Pulse IO_UPDATE to latch config
        # self.dds.io_update.pulse(1 * us)

        # # self.dds.set_cfr1()  # clear back to default (drg_load_lrr=0)
        # # self.dds.io_update.pulse(1 * us)


        # # Optional: set DRCTL low so the ramp auto-reverses (handled by CPLD usually)
        # # self.dds.cfg_drctl(False)
        # # self.dds.cfg_drhold(False)


        # # Stop DRG
        # # self.dds.set_cfr2(drg_destination=0, drg_enable=0)
        # # self.dds.io_update.pulse(1 * us)


        print("Test complete!")
        print(self.dds.cpld.proto_rev)
