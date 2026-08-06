export const navigationItems = [
  { label: 'Dashboard', path: '/dashboard', roles: ['SUPER_ADMIN', 'SCHOOL_ADMIN', 'TEACHER', 'GUIDANCE'] },
  { label: 'Students', path: '/students', roles: ['SUPER_ADMIN', 'SCHOOL_ADMIN', 'TEACHER', 'GUIDANCE'] },
  { label: 'Academics', path: '/academics', roles: ['SUPER_ADMIN', 'SCHOOL_ADMIN', 'TEACHER', 'GUIDANCE'] },
  { label: 'Attendance', path: '/attendance', roles: ['SUPER_ADMIN', 'SCHOOL_ADMIN', 'TEACHER', 'GUIDANCE'] },
  { label: 'Behavior', path: '/behavior', roles: ['SUPER_ADMIN', 'SCHOOL_ADMIN', 'TEACHER', 'GUIDANCE'] },
  { label: 'Interventions', path: '/interventions', roles: ['SUPER_ADMIN', 'SCHOOL_ADMIN', 'TEACHER', 'GUIDANCE'] },
  { label: 'Predictions', path: '/predictions', roles: ['SUPER_ADMIN', 'SCHOOL_ADMIN', 'TEACHER', 'GUIDANCE'] },
  { label: 'Reports', path: '/reports', roles: ['SUPER_ADMIN', 'SCHOOL_ADMIN', 'GUIDANCE'] },
  { label: 'Administration', path: '/admin', roles: ['SUPER_ADMIN', 'SCHOOL_ADMIN'] },
]
