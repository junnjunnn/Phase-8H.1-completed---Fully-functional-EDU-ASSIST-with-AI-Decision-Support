import { Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from '../components/layout/AppLayout'
import { ProtectedRoute } from './ProtectedRoute'
import { RoleRoute } from './RoleRoute'
import { Login } from '../pages/auth/Login'
import { Dashboard } from '../pages/dashboard/Dashboard'
import { StudentsPage } from '../pages/students/StudentsPage'
import { StudentDetailPage } from '../pages/students/StudentDetailPage'
import { AcademicsPage } from '../pages/academics/AcademicsPage'
import { AttendancePage } from '../pages/attendance/AttendancePage'
import { BehaviorPage } from '../pages/behavior/BehaviorPage'
import { InterventionsPage } from '../pages/interventions/InterventionsPage'
import { PredictionsPage } from '../pages/predictions/PredictionsPage'
import { ReportsPage } from '../pages/reports/ReportsPage'

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
          <Route path="/attendance" element={<AttendancePage />} />
          <Route path="/behavior" element={<BehaviorPage />} />
          <Route path="/interventions" element={<InterventionsPage />} />
          <Route path="/predictions" element={<PredictionsPage />} />
          <Route element={<RoleRoute allowedRoles={['SUPER_ADMIN', 'SCHOOL_ADMIN', 'GUIDANCE']} />}>
            <Route path="/reports" element={<ReportsPage />} />
          </Route>
        </Route>
      </Route>
    </Routes>
  )
}
