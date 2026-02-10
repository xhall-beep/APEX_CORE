#ifndef REECH_BYPASS_H
#define REECH_BYPASS_H
#include <errno.h>
#include <sys/types.h>
#include <pwd.h>

// Neutralize Filesystem/IO Ghosts
#define close_range(a, b, c) (errno = ENOSYS, -1)
#define copy_file_range(a,b,c,d,e,f) (errno = ENOSYS, -1)
#define preadv2(a,b,c,d,e) (errno = ENOSYS, -1)
#define pwritev2(a,b,c,d,e) (errno = ENOSYS, -1)

// Neutralize Password DB Ghosts (Android Bionic lacks these)
#define setpwent() ((void)0)
#define endpwent() ((void)0)
#define getpwent() (NULL)

// Neutralize System/Thread Ghosts
#define getloadavg(a,b) (errno = ENOSYS, -1)
#define fexecve(a, b, c) (errno = ENOSYS, -1)
#define sem_clockwait(sem, clock, timeout) sem_timedwait(sem, timeout)

#endif
#ifndef FFI_BYPASS
#define FFI_BYPASS
// Ensure libffi doesn't trip on missing sys/mman.h stubs if they occur
#include <sys/mman.h>
#endif
