import { Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from '../components/layout/AppLayout'
import { ProtectedRoute } from './ProtectedRoute'
import { RoleRoute } from './RoleRoute'
import { Login } from '../pages/auth/Login'
import { Dashboard } from '../pages/dashboard/Dashboard'
import { StudentsPage } from '../pages/students/StudentsPage'
import { StudentDetailPage } from '../pages/students/StudentDetailPage'
import { AcademicsPage } from '../pages/academics/AcademicsPage'
import { AcademicStructurePage } from '../pages/academics/AcademicStructurePage'
import { GradeEncodingPage } from '../pages/academics/GradeEncodingPage'
import { MyClassesPage } from '../pages/academics/MyClassesPage'
import { AttendancePage } from '../pages/attendance/AttendancePage'
import { AttendanceEncodingPage } from '../pages/attendance/AttendanceEncodingPage'
import { BehaviorPage } from '../pages/behavior/BehaviorPage'
import { BehaviorEncodingPage } from '../pages/behavior/BehaviorEncodingPage'
import { InterventionsPage } from '../pages/interventions/InterventionsPage'
import { PredictionsPage } from '../pages/predictions/PredictionsPage'
import { ReportsPage } from '../pages/reports/ReportsPage'
import { UsersPage } from '../pages/users/UsersPage'
import { ProfilePage } from '../pages/profile/ProfilePage'
import { AccessDeniedPage } from '../pages/errors/AccessDeniedPage'
import { NotFoundPage } from '../pages/errors/NotFoundPage'
import { ComingSoonCard } from '../components/common/ComingSoonCard'

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
          <Route path="/my-classes" element={<MyClassesPage />} />
          <Route element={<RoleRoute allowedRoles={['SUPER_ADMIN', 'SCHOOL_ADMIN']} />}>
            <Route path="/academic-structure" element={<AcademicStructurePage />} />
          </Route>
          <Route path="/academics/encode" element={<GradeEncodingPage />} />
          <Route path="/attendance" element={<AttendancePage />} />
          <Route path="/attendance/encode" element={<AttendanceEncodingPage />} />
          <Route path="/behavior" element={<BehaviorPage />} />
          <Route path="/behavior/encode" element={<BehaviorEncodingPage />} />
          <Route path="/interventions" element={<InterventionsPage />} />
          <Route path="/predictions" element={<PredictionsPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/admin" element={<ComingSoonCard title="Admin Console" description="Administrative workflows and system controls are being finalized for a more complete operations experience." features={['User oversight', 'Policy controls', 'School-wide reporting', 'Audit visibility']} />} />
          <Route element={<RoleRoute allowedRoles={['SUPER_ADMIN', 'SCHOOL_ADMIN']} />}>
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
