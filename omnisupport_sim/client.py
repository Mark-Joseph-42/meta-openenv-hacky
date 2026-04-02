"""EnvClient subclass for OmniSupport-Sim."""
from openenv.core.env_client import EnvClient
from omnisupport_sim.models import OmniSupportAction, OmniSupportObservation

class OmniSupportEnv(EnvClient):
    action_type = OmniSupportAction
    observation_type = OmniSupportObservation
