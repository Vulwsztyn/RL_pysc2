import sys
from absl import flags
from pysc2.env import sc2_env, environment
from pysc2.lib import actions, features
import torch
import matplotlib.pyplot as plt
from ACTION import actAgent2Pysc2, no_operation
from STATE import calc_distance
import numpy as np
import random
import tensorflow as tf
from collections import deque
import time
import math
from A2C import A2C


# Define the constant
_PLAYER_RELATIVE = features.SCREEN_FEATURES.player_relative.index
_UNIT_TYPE = features.SCREEN_FEATURES.unit_type.index
_SELECTED_UNIT = features.SCREEN_FEATURES.selected.index
friendly = 1
neutral = 3
_SELECT_RECT = actions.FUNCTIONS.select_rect.id
_SELECT_POINT = actions.FUNCTIONS.select_point.id
_SELECT_ARMY = actions.FUNCTIONS.select_army.id
_MOVE_SCREEN = actions.FUNCTIONS.Move_screen.id
_NO_OP           = actions.FUNCTIONS.no_op.id
_ATTACK_MINIMAP = actions.FUNCTIONS.Attack_minimap.id
_SELECT_ALL  = [0]
_NOT_QUEUED  = [0]
step_mul = 8
FLAGS = flags.FLAGS
EPISODES = 10000

def train():
    FLAGS(sys.argv)
    with sc2_env.SC2Env(map_name="MoveToBeacon", step_mul=step_mul, visualize=True,
                        agent_interface_format=sc2_env.AgentInterfaceFormat(
                            feature_dimensions=sc2_env.Dimensions(screen=64, minimap=64))) as env:
        a2c = torch.load("a2cAgent_Trained_Model_20190714-172511  9001.pth")
        rwd = []
        for episodes in range(EPISODES):
            done = False
            obs = env.reset()
            _,__,___,state = calc_distance(obs)
            print('episode start')
            global_step = 0
            reward = 0
            cum_rew = 0
            score_cum = 0
            while not done:
                global_step += 1
		#selecting marine
                while not 331 in obs[0].observation["available_actions"]:
                    actionss = actions.FunctionCall(_SELECT_ARMY, [_SELECT_ALL])
                    obs = env.step(actions=[actionss])
                _, action_x, __,___,action_y,____ = a2c.choose_action(state)
                obs = env.step(actions =[actions.FunctionCall(_MOVE_SCREEN, [_NOT_QUEUED, [action_x,action_y]])])
                _, __, distance, next_state = calc_distance(obs)
                if global_step == 1:
                    pre_distance = distance
		        #reward enginnering part
                reward = -(distance - pre_distance)
                if obs[0].reward == 1:
                    reward = 100

                if obs[0].step_type == environment.StepType.LAST:
                        done = True
                a2c.learn(reward ,state,next_state,action_x,action_y)
                cum_rew = reward + cum_rew
                score_cum += obs[0].reward
                state = next_state
                pre_distance = distance

            print("episode: ", episodes, "reward: ", cum_rew, "score: ", score_cum)
            if episodes%1000==1:
                timestr = time.strftime("%Y%m%d-%H%M%S")
                nn_filename = "a2cAgent_Trained_Model_" + timestr + "  "+str(episodes)+ ".pth"
                torch.save(a2c, nn_filename)

if __name__ == '__main__':
    train()

