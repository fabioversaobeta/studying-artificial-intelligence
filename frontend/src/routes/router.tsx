import { createBrowserRouter } from 'react-router-dom'
import { AppLayout } from '@/layouts/app-layout'
import { AuthLayout } from '@/layouts/auth-layout'
import { ProtectedRoute, GuestOnlyRoute } from '@/routes/protected-route'
import { LoginPage } from '@/pages/login-page'
import { RegisterPage } from '@/pages/register-page'
import { DashboardPage } from '@/pages/dashboard-page'
import { SubjectsPage } from '@/pages/subjects-page'
import { SubjectDetailPage } from '@/pages/subject-detail-page'
import { GoalsPage } from '@/pages/goals-page'
import { ReviewsPage } from '@/pages/reviews-page'
import { AchievementsPage } from '@/pages/achievements-page'
import { SettingsPage } from '@/pages/settings-page'
import { LearningPathsPage, LearningPathDetailPage } from '@/pages/learning-paths-page'

export const router = createBrowserRouter([
  {
    element: <GuestOnlyRoute />,
    children: [
      {
        element: <AuthLayout><LoginPage /></AuthLayout>,
        path: '/login',
      },
      {
        element: <AuthLayout><RegisterPage /></AuthLayout>,
        path: '/register',
      },
    ],
  },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: '/', element: <DashboardPage /> },
          { path: '/subjects', element: <SubjectsPage /> },
          { path: '/subjects/:id', element: <SubjectDetailPage /> },
          { path: '/goals', element: <GoalsPage /> },
          { path: '/reviews', element: <ReviewsPage /> },
          { path: '/achievements', element: <AchievementsPage /> },
          { path: '/learning-paths', element: <LearningPathsPage /> },
          { path: '/learning-paths/:slug', element: <LearningPathDetailPage /> },
          { path: '/settings', element: <SettingsPage /> },
        ],
      },
    ],
  },
])
