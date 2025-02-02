import numpy as np
from gym import utils
from gym.envs.mujoco import mujoco_env

class HopperEnv(mujoco_env.MujocoEnv, utils.EzPickle):
    def __init__(self):
        print("in hopper env")
        mujoco_env.MujocoEnv.__init__(self, 'hopper.xml', 4)
        utils.EzPickle.__init__(self)

    def step(self, a):
        posbefore = self.sim.data.qpos[0]
        self.do_simulation(a, self.frame_skip)
        posafter, height, ang = self.sim.data.qpos[0:3]
        alive_bonus = 1.0
        reward = (posafter - posbefore) / self.dt
        reward += alive_bonus
        reward -= 1e-3 * np.square(a).sum()
        s = self.state_vector()
        done = not (np.isfinite(s).all() and (np.abs(s[2:]) < 100).all() and
                    (height > .7) and (abs(ang) < .2))
        ob = self._get_obs()
        return ob, reward, done, {}

    def _get_obs(self):
        return np.concatenate([
            self.sim.data.qpos.flat[1:],
            np.array(self.sim.data.qvel.flat)
            # np.clip(self.sim.data.qvel.flat, -10, 10)
        ])

    def reset_model(self):
        qpos = self.init_qpos + self.np_random.uniform(low=-.005, high=.005, size=self.model.nq)
        qvel = self.init_qvel + self.np_random.uniform(low=-.005, high=.005, size=self.model.nv)
        self.set_state(qpos, qvel)
        return self._get_obs()

    def viewer_setup(self):
        self.viewer.cam.trackbodyid = 2
        self.viewer.cam.distance = self.model.stat.extent * 0.75
        self.viewer.cam.lookat[2] = 1.15
        self.viewer.cam.elevation = -20

    def set_ob_and_step(self, ob, act):
        qpos = ob[:self.model.nq - 1]
        # self.sim.data.qpos[0]]
        qpos = np.concatenate(([0.0], qpos))
        qvel = ob[self.model.nq - 1:]
        self.set_state(qpos, qvel)
        ob, reward, done, _ = self.step(act)
        return ob, reward, done, {}

    def step_with_state(self, state, a):
        qpos, qvel = state
        self.set_state(qpos, qvel)
        return self.step(a)

if __name__ =='__main__':
    env = HopperEnv()
    int_obs = env.reset()
    for i in range(3000):
        a = env.action_space.sample()
        ob, reward, done, _ = env.step(a)
        ob2, reward, done, _ = env.set_ob_and_step(int_obs, a)
        ob3, reward, done, _ = env.set_ob_and_step(int_obs, a)
        if not np.all(ob - ob2) < 1e-10:
            print("error to step {}".format(ob - ob2))
        if not np.all(ob3 - ob2) < 1e-10:
            print("error to repeat set_ob_and_step {}".format(ob3 - ob2))
        int_obs = ob3