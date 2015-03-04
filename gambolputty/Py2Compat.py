# -*- coding: utf-8 -*-

def exec_function(string_to_execute, global_env={}, local_env={}):
    exec string_to_execute in global_env, local_env