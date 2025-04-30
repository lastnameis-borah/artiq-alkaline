from artiq.experiment import *

class TestCore(EnvExperiment):
    def build(self):
        self.setattr_device("core")
    
    @kernel
    def run(self):
        self.core.reset()
        self.core.break_realtime()

        print("Hello Possible!")