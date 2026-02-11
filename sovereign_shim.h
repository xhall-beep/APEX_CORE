#ifndef SOVEREIGN_SHIM_H
#define SOVEREIGN_SHIM_H
#include <time.h>
#include <semaphore.h>
#include <errno.h>
#include <unistd.h>
#include <sys/syscall.h>

static inline int sem_clockwait(sem_t *sem, clockid_t clockid, const struct timespec *abs_timeout) {
    return sem_timedwait(sem, abs_timeout);
}

#ifndef SYS_close_range
#define SYS_close_range 436
#endif
static inline int close_range(unsigned int first, unsigned int last, unsigned int flags) {
    return syscall(SYS_close_range, first, last, flags);
}
#endif
