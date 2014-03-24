Base Classes
==========

#####BaseModule

Base class for all GambolPutty modules that will run not run.
If you happen to override one of the methods defined here, be sure to know what you
are doing ;) You have been warned ;)

id: Set id of module if more than one module of the same type is used.
filter: Set input filter. Only matching events will be handled by the module.
receivers: Set receivers for output of module. If not set, output will be send to next module in configuration.
filter: Set output filter. Only matching events will be send to receiver.

Configuration template:

    - SomeModuleName:
        id:                                       # <default: ""; type: string; is: optional>
        filter:                                   # <default: None; type: None||string; is: optional>
        ...
        receivers:
         - ModuleName:
             filter:                              # <default: None; type: None||string; is: optional>
         - ModuleAlias

#####BaseThreadedModule

Base class for all GambolPutty modules that will run as separate threads.
If you happen to override one of the methods defined here, be sure to know what you
are doing ;) You have been warned ;)

Running a module as a thread should only be done if the task is mainly I/O bound or the
used python code will release the GIL during its man work.
Otherwise a threaded module is prone to slow everything down.

id: Set id of module if more than one module of the same type is used.
filter: Set input filter. Only matching events will be handled by the module.
pool_size: Set number of worker threads.
queue_size: Set maximum number of event, waiting in queue.
receivers: Set receivers for output of module. If not set, output will be send to next module in configuration.
filter: Set output filter. Only matching events will be send to receiver.

Configuration template:

    - SomeModuleName:
        id:                                       # <default: ""; type: string; is: optional>
        filter:                                   # <default: None; type: None||string; is: optional>
        pool_size: 4                              # <default: None; type: None||integer; is: optional>
        queue_size: 20                            # <default: None; type: None||integer; is: optional>
        ...
        receivers:
         - ModuleName:
             filter:                              # <default: None; type: None||string; is: optional>
         - ModuleAlias

#####BaseMultiProcessModule

Base class for all GambolPutty modules that will run as separate processes.
If you happen to override one of the methods defined here, be sure to know what you
are doing. You have been warned ;)

Running a module as its own process solves GIL related problems and allows to utilize more
than just a single core on a multicore machine.
But this comes with some (not so small) drawbacks. Passing data to and from a process
involves pickling/unpickling. This results in a major overhead compared to normal queues
in a threaded environment. To elevate this problem a bit, mp modules use a buffered queue,
so not every single event will get pickled/unpickled.

id: Set id of module if more than one module of the same type is used.
filter: Set input filter. Only matching events will be handled by the module.
pool_size: Set number of worker threads.
queue_size: Set maximum number of event, waiting in queue.
receivers: Set receivers for output of module. If not set, output will be send to next module in configuration.
filter: Set output filter. Only matching events will be send to receiver.

Configuration template:

    - SomeModuleName:
        id:                                       # <default: ""; type: string; is: optional>
        filter:                                   # <default: None; type: None||string; is: optional>
        pool_size: 4                              # <default: None; type: None||integer; is: optional>
        queue_size: 20                            # <default: None; type: None||integer; is: optional>
        ...
        receivers:
         - ModuleName:
             filter:                              # <default: None; type: None||string; is: optional>
         - ModuleAlias