import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from './stores/auth';
import LoginView from './views/LoginView.vue';
import DashboardView from './views/DashboardView.vue';
import ConfigView from './views/ConfigView.vue';
import LogsView from './views/LogsView.vue';
import UsersView from './views/UsersView.vue';
import SettingsView from './views/SettingsView.vue';
import AuditView from './views/AuditView.vue';
import StatsView from './views/StatsView.vue';
import LogFilesView from './views/LogFilesView.vue';
import GroupsView from './views/GroupsView.vue';
import HostDashboardView from './views/HostDashboardView.vue';
import ManualsView from './views/ManualsView.vue';
import SystemLogsView from './views/SystemLogsView.vue';
import ReceiverView from './views/ReceiverView.vue';

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: { public: true },
  },
  {
    path: '/',
    name: 'Dashboard',
    component: DashboardView,
    meta: { requiresAuth: true },
  },
  {
    path: '/config',
    name: 'Config',
    component: ConfigView,
    meta: { requiresAuth: true },
  },
  {
    path: '/receiver',
    name: 'Receiver',
    component: ReceiverView,
    meta: { requiresAuth: true },
  },
  {
    path: '/logs',
    name: 'Logs',
    component: LogsView,
    meta: { requiresAuth: true },
  },
  {
    path: '/users',
    name: 'Users',
    component: UsersView,
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: SettingsView,
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/audit',
    name: 'Audit',
    component: AuditView,
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/stats',
    name: 'Stats',
    component: StatsView,
    meta: { requiresAuth: true },
  },
  {
    path: '/logfiles',
    name: 'LogFiles',
    component: LogFilesView,
    meta: { requiresAuth: true },
  },
  {
    path: '/my-hosts',
    name: 'HostDashboard',
    component: HostDashboardView,
    meta: { requiresAuth: true },
  },
  {
    path: '/groups',
    name: 'Groups',
    component: GroupsView,
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/manuals',
    name: 'Manuals',
    component: ManualsView,
    meta: { requiresAuth: true },
  },
  {
    path: '/syslogs',
    name: 'SystemLogs',
    component: SystemLogsView,
    meta: { requiresAuth: true, requiresAdmin: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore();
  if (auth.token) {
    await auth.initialize();
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return next({ name: 'Login' });
  }

  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return next({ name: 'Dashboard' });
  }

  if (to.name === 'Login' && auth.isAuthenticated) {
    return next({ name: 'Dashboard' });
  }

  next();
});

export default router;
