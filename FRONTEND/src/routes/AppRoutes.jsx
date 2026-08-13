import { Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from '../components/layout/AppLayout'
import { ProtectedRoute } from './ProtectedRoute'
import { RoleRoute } from './RoleRoute'
import { Login } from '../pages/auth/Login'
import { Dashboard } from '../pages/dashboard/Dashboard'
import { StudentsPage } from '../pages/students/StudentsPage'
import { StudentDetailPage } from '../pages/students/StudentDetailPage'
import { EnrollmentPage } from '../pages/students/EnrollmentPage'
import { AcademicsPage } from '../pages/academics/AcademicsPage'
import { AcademicStructurePage } from '../pages/academics/AcademicStructurePage'
import { AcademicYearsPage } from '../pages/academics/AcademicYearsPage'
import { GradeLevelsPage } from '../pages/academics/GradeLevelsPage'
import { SectionsPage } from '../pages/academics/SectionsPage'
import { SubjectsPage } from '../pages/academics/SubjectsPage'
import { GradeEncodingPage } from '../pages/academics/GradeEncodingPage'
import { MyClassesPage } from '../pages/academics/MyClassesPage'
import { TeacherAssignmentsPage } from '../pages/academics/TeacherAssignmentsPage'
import { AttendancePage } from '../pages/attendance/AttendancePage'
import { AttendanceEncodingPage } from '../pages/attendance/AttendanceEncodingPage'
import { BehaviorPage } from '../pages/behavior/BehaviorPage'
import { BehaviorEncodingPage } from '../pages/behavior/BehaviorEncodingPage'
import { InterventionsPage } from '../pages/interventions/InterventionsPage'
import { PredictionsPage } from '../pages/predictions/PredictionsPage'
import { ReportsPage } from '../pages/reports/ReportsPage'
import { UsersPage } from '../pages/users/UsersPage'
import { ProfilePage } from '../pages/profile/ProfilePage'
import { AuditLogsPage } from '../pages/admin/AuditLogsPage'
import { SettingsPage } from '../pages/settings/SettingsPage'
import { NotFoundPage } from '../pages/errors/NotFoundPage'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/students" element={<StudentsPage />} />
          <Route path="/students/:id" element={<StudentDetailPage />} />
          <Route path="/academics" element={<AcademicsPage />} />
          <Route element={<RoleRoute allowedRoles={['TEACHER']} />}>
            <Route path="/my-classes" element={<MyClassesPage />} />
          </Route>
          <Route element={<RoleRoute allowedRoles={['SUPER_ADMIN', 'SCHOOL_ADMIN', 'REGISTRAR']} />}>
            <Route path="/academic-structure" element={<AcademicStructurePage />} />
            <Route path="/academic-years" element={<AcademicYearsPage />} />
            <Route path="/grade-levels" element={<GradeLevelsPage />} />
            <Route path="/sections" element={<SectionsPage />} />
            <Route path="/subjects" element={<SubjectsPage />} />
            <Route path="/teacher-assignments" element={<TeacherAssignmentsPage />} />
            <Route path="/enrollment" element={<EnrollmentPage />} />
          </Route>
          <Route path="/academics/encode" element={<GradeEncodingPage />} />
          <Route path="/attendance" element={<AttendancePage />} />
          <Route path="/attendance/encode" element={<AttendanceEncodingPage />} />
          <Route path="/behavior" element={<BehaviorPage />} />
          <Route path="/behavior/encode" element={<BehaviorEncodingPage />} />
          <Route path="/interventions" element={<InterventionsPage />} />
          <Route path="/predictions" element={<PredictionsPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route element={<RoleRoute allowedRoles={['SUPER_ADMIN', 'SCHOOL_ADMIN']} />}>
            <Route path="/admin" element={<AuditLogsPage />} />
            <Route path="/users" element={<UsersPage />} />
          </Route>
          <Route element={<RoleRoute allowedRoles={['SUPER_ADMIN', 'SCHOOL_ADMIN', 'GUIDANCE', 'TEACHER']} />}>
            <Route path="/reports" element={<ReportsPage />} />
          </Route>
        </Route>
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
