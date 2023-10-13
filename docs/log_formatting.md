# Log Formatting Standards

This project assumes Lmod log messages are written to disk using the following format.
Log entries **must** follow this format to be parsable by the `lmod-ingest` application.

```text
[SYSLOG PREFIX] user=[USERNAME] jobid=[JOBID] module=[PACKAGE]/[VERSION] path=[MODULEPATH] host=[HOSTNAME] time=[UTC]
```

Individual field values are defined as follows:

| Field           | Description                                                              |
|-----------------|--------------------------------------------------------------------------|
| `SYSLOG PREFIX` | A system specific message prefix added by syslog. This value is ignored. |
| `USERNAME`      | The name of the user who loaded the module.                              |
| `JOBID`         | The nullable (`nil`) ID of the slurm job the module was loaded from.     |
| `PACKAGE`       | The name of the package loaded via lmod.                                 |
| `VERSION`       | The version of the pacakge loaded via lmod.                              |
| `MODULEPATH`    | The path of the loaded module file.                                      |
| `HOSTNAME`      | The machine hostname where the module was loaded.                        |
| `UTC`           | The UTC time the module was loaded.                                      |

## Setting the Log Format

If your format differs from the above, you must change it by editing the `SitePackage.lua` file.
The specific location of this file will vary depending on your Slurm cluster setup.

Appending the following code to the bottom of your `SitePackage.lua` file will send lmod messages to syslog using the required format.
Note the slurm Job ID is determined using the nullable environmental variable `SLURM_JOB_ID` 
(and not the older, deprecated variable `SLURM_JOBID`).

```lua
--------------------------------------------------------------------------

require("lmod_system_execute")
local hook    = require("Hook")
local uname   = require("posix").uname
-- Cosmic class not available in the CRC current default lmod (6.6.3), introduced in 7.1.8
--   allows fetching of globals and defaults, see 'host' assignment in load_hook()
-- local cosmic  = require("Cosmic"):singleton()
-- local syshost = cosmic:value("LMOD_SYSHOST")

-- By using the hook.register function, this function "load_hook" is called
-- ever time a module is loaded with the file name and the module name.

local s_msgA = {}

function load_hook(t)
   -- the arg t is a table:
   --     t.modFullName:  the module full name: (i.e: gcc/4.7.2)
   --     t.fn:           The file name: (i.e /apps/modulefiles/Core/gcc/4.7.2.lua)

   if (mode() ~= "load") then return end
   local user        = os.getenv("USER")
   local jobid       = os.getenv("SLURM_JOB_ID") or "nil"
   local host        = uname("%n")
   local currentTime = epoch()
   local msg         = string.format("'user=%s jobid=%s module=%s path=%s host=%s time=%f'",
                                     user, jobid, t.modFullName, t.fn, host, currentTime)
   local a           = s_msgA
   a[#a+1]           = msg
end

hook.register("load",load_hook)

function report_loads()

   local sys         = os.getenv("LMOD_sys") or "Linux"
   if (sys == "Linux") then
      local a = s_msgA
      for i = 1,#a do
         local msg = a[i]
         lmod_system_execute("logger -t ModuleUsageTracking -p local0.info " .. msg)
      end
   end

end

ExitHookA.register(report_loads)
```
