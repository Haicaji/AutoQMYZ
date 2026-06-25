import React, { useState, useEffect, useRef } from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Container,
  Paper,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Card,
  CardContent,
  CardActions,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Switch,
  Chip,
  Snackbar,
  Alert,
  Tooltip,
  Autocomplete
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Settings as SettingsIcon,
  People as PeopleIcon,
  QueuePlayNext as QueueIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
  Terminal as TerminalIcon,
  CheckCircle as SuccessIcon,
  Cancel as FailedIcon,
  HourglassEmpty as PendingIcon,
  Pause as PauseIcon,
  PowerSettingsNew as PowerIcon,
  ArrowUpward as ArrowUpwardIcon,
  ArrowDownward as ArrowDownwardIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon
} from '@mui/icons-material';

// Premium dark theme
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#a78bfa', // Light violet
    },
    secondary: {
      main: '#14b8a6', // Teal
    },
    background: {
      default: '#0f172a', // Slate 900
      paper: '#1e293b', // Slate 800
    },
    success: {
      main: '#10b981',
    },
    error: {
      main: '#f43f5e',
    },
    warning: {
      main: '#f59e0b',
    },
    text: {
      primary: '#f8fafc',
      secondary: '#94a3b8',
    }
  },
  typography: {
    fontFamily: '"Outfit", "Inter", "Roboto", sans-serif',
    h5: {
      fontWeight: 700,
      letterSpacing: '0.5px'
    },
    h6: {
      fontWeight: 600,
    },
    button: {
      textTransform: 'none',
      fontWeight: 600
    }
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '8px 16px',
        }
      }
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          backgroundImage: 'none',
          border: '1px solid #334155'
        }
      }
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          backgroundImage: 'none',
          border: '1px solid #334155'
        }
      }
    }
  }
});

const DRAWER_WIDTH = 240;
const API_BASE = window.location.port === '5173' ? 'http://127.0.0.1:8000' : '';

const STRATEGY_NAMES = {
  db: '题库回答 (从本地已存题库中查找答案)',
  ai: 'AI作答 (使用配置的大语言模型进行作答)',
  manual: '人工作答 (控制台提示输入答案，支持超时自动跳过)',
  random: '随机回答 (没有答案时，随机选择一个作为保底作答)'
};

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [verifyingUser, setVerifyingUser] = useState(null);

  const maskAccount = (account) => {
    if (!account) return "";
    const str = String(account);
    if (/^\d{11}$/.test(str)) {
      return str.slice(0, 3) + "****" + str.slice(7);
    }
    if (str.length > 4) {
      return str.slice(0, 2) + "***" + str.slice(-2);
    }
    if (str.length > 2) {
      return str.slice(0, 1) + "**" + str.slice(-1);
    }
    return "**";
  };
  
  // Queue state
  const [queue, setQueue] = useState({ items: [], active: false });
  const [selectedAnswers, setSelectedAnswers] = useState({}); // task_id -> [selected options]
  
  // Config state
  const [config, setConfig] = useState({
    api_key: '',
    base_url: '',
    model: '',
    task_parallel_limit: 1,
    user_parallel_limit: 1,
    answer_priority: ['db', 'ai', 'manual', 'random'],
    manual_timeout: 30
  });
  
  // Dialog states
  const [openCreateUser, setOpenCreateUser] = useState(false);
  const [newUser, setNewUser] = useState({ username: '', account: '', password: '', verify_request: '' });
  
  const [openEditUser, setOpenEditUser] = useState(false);
  const [editUserForm, setEditUserForm] = useState({ account: '', password: '', verify_request: '', UA: '' });
  
  const [openTaskDialog, setOpenTaskDialog] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [taskForm, setTaskForm] = useState({
    course_name: '',
    aim_questions_num_total: 100,
    low_right_rate: 0.7,
    top_right_rate: 0.9,
    min_question_time: 8.0,
    current_question_num: 0,
    current_right_num: 0,
    finish: false
  });
  
  const [availableCourses, setAvailableCourses] = useState([]);
  
  // Log states
  const [activeLogId, setActiveLogId] = useState(null);
  const [activeLogContent, setActiveLogContent] = useState('');
  const logEndRef = useRef(null);
  const [logStats, setLogStats] = useState({ system_log_size: '0 B', task_logs_size: '0 B', task_logs_count: 0 });
  const [openClearLogsConfirm, setOpenClearLogsConfirm] = useState(false);
  
  // Notification state
  const [toast, setToast] = useState({ open: false, message: '', severity: 'success' });

  // ----------------- Data Loading -----------------
  const fetchUsers = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/users`);
      if (res.ok) {
        const data = await res.json();
        setUsers(data);
        
        // Auto update selectedUser reference if it matches
        if (selectedUser) {
          const updated = data.find(u => u.username === selectedUser.username);
          if (updated) {
            setSelectedUser(updated);
          } else {
            setSelectedUser(null);
          }
        }
      }
    } catch (e) {
      console.error("Fetch users error", e);
    }
  };

  const fetchQueue = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/queue`);
      if (res.ok) {
        const data = await res.json();
        setQueue(data);
      }
    } catch (e) {
      console.error("Fetch queue error", e);
    }
  };

  const fetchConfig = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/config`);
      if (res.ok) {
        const data = await res.json();
        setConfig(data);
      }
    } catch (e) {
      console.error("Fetch config error", e);
    }
  };

  const fetchAvailableCourses = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/courses`);
      if (res.ok) {
        const data = await res.json();
        setAvailableCourses(data);
      }
    } catch (e) {
      console.error("Fetch courses error", e);
    }
  };

  const fetchLogs = async (taskId) => {
    try {
      const res = await fetch(`${API_BASE}/api/logs/${taskId}`);
      if (res.ok) {
        const data = await res.json();
        setActiveLogContent(data.logs);
      }
    } catch (e) {
      console.error("Fetch logs error", e);
    }
  };

  const fetchLogStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/logs/stats`);
      if (res.ok) {
        const data = await res.json();
        setLogStats(data);
      }
    } catch (e) {
      console.error("Fetch log stats error", e);
    }
  };

  const handleClearLogs = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/logs/clear`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        handleShowToast(data.message || "历史日志清理完成！");
        fetchLogStats();
      } else {
        handleShowToast("清理日志失败", "error");
      }
    } catch (e) {
      handleShowToast("网络请求异常", "error");
    } finally {
      setOpenClearLogsConfirm(false);
    }
  };

  // Initial loads
  useEffect(() => {
    fetchUsers();
    fetchQueue();
    fetchConfig();
    fetchAvailableCourses();
  }, []);

  // Polling queue state
  useEffect(() => {
    const timer = setInterval(() => {
      fetchQueue();
      fetchUsers();
    }, 1000);
    return () => clearInterval(timer);
  }, [selectedUser]);

  // Polling logs if open
  useEffect(() => {
    if (!activeLogId) return;
    const timer = setInterval(() => {
      fetchLogs(activeLogId);
    }, 1000);
    return () => clearInterval(timer);
  }, [activeLogId]);

  // Scroll to bottom of log dialog
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [activeLogContent]);

  // ----------------- Handlers -----------------
  const handleShowToast = (message, severity = 'success') => {
    setToast({ open: true, message, severity });
  };

  const handleCreateUser = async () => {
    if (!newUser.username || !newUser.account || !newUser.password) {
      handleShowToast("请填写用户名、账号与密码", "warning");
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newUser)
      });
      const data = await res.json();
      if (res.ok) {
        handleShowToast(data.message);
        setOpenCreateUser(false);
        setNewUser({ username: '', account: '', password: '', verify_request: '' });
        fetchUsers();
      } else {
        handleShowToast(data.detail || "创建失败", "error");
      }
    } catch (e) {
      handleShowToast("网络请求异常", "error");
    }
  };

  const handleOpenEditUser = () => {
    if (!selectedUser) return;
    setEditUserForm({
      account: selectedUser.account,
      password: '', // empty means keep unchanged
      verify_request: selectedUser.verify_request || '',
      UA: selectedUser.UA || ''
    });
    setOpenEditUser(true);
  };

  const handleSaveEditUser = async () => {
    if (!editUserForm.account) {
      handleShowToast("账号不能为空", "warning");
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/users/${selectedUser.username}/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(editUserForm)
      });
      const data = await res.json();
      if (res.ok) {
        handleShowToast(data.message);
        setOpenEditUser(false);
        fetchUsers();
      } else {
        handleShowToast(data.detail || "修改失败", "error");
      }
    } catch (e) {
      handleShowToast("网络请求异常", "error");
    }
  };

  const handleDeleteUser = async (username) => {
    if (!window.confirm(`确定要删除用户 "${username}" 吗？`)) return;
    try {
      const res = await fetch(`${API_BASE}/api/users/${username}`, { method: 'DELETE' });
      const data = await res.json();
      if (res.ok) {
        handleShowToast(data.message);
        if (selectedUser?.username === username) {
          setSelectedUser(null);
        }
        fetchUsers();
      } else {
        handleShowToast(data.detail || "删除失败", "error");
      }
    } catch (e) {
      handleShowToast("网络请求异常", "error");
    }
  };

  const handleVerifyUserLogin = async (username) => {
    if (verifyingUser) return;
    setVerifyingUser(username);
    handleShowToast("正在通过后台无头浏览器登录并验证连接，请稍候...", "info");
    try {
      const res = await fetch(`${API_BASE}/api/users/${username}/verify`, {
        method: 'POST'
      });
      const data = await res.json();
      if (res.ok && data.success) {
        const coursesStr = data.courses && data.courses.length > 0 
          ? `，成功获取课程：${data.courses.join('、')}`
          : "，但未读取到课程";
        handleShowToast(`验证成功${coursesStr}`, "success");
        fetchUsers();
      } else {
        handleShowToast(data.message || "登录验证失败，请检查账号密码是否失效", "error");
      }
    } catch (e) {
      handleShowToast("网络请求异常", "error");
    } finally {
      setVerifyingUser(null);
    }
  };

  const handleSaveConfig = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      const data = await res.json();
      if (res.ok) {
        handleShowToast(data.message);
        fetchConfig();
      } else {
        handleShowToast(data.detail || "保存失败", "error");
      }
    } catch (e) {
      handleShowToast("网络请求异常", "error");
    }
  };

  // Task Actions
  const handleOpenAddTask = () => {
    if (!selectedUser || selectedUser.login_status !== 'verified') {
      handleShowToast("在创建或添加答题任务课程前，请先点击【验证登录】成功验证您的账户凭证！", "warning");
      return;
    }
    fetchAvailableCourses();
    setEditingTask(null);
    setTaskForm({
      course_name: '',
      aim_questions_num_total: 100,
      low_right_rate: 0.7,
      top_right_rate: 0.9,
      min_question_time: 8.0,
      current_question_num: 0,
      current_right_num: 0,
      finish: false
    });
    setOpenTaskDialog(true);
  };

  const handleOpenEditTask = (task) => {
    setEditingTask(task);
    setTaskForm({ ...task });
    setOpenTaskDialog(true);
  };

  const handleSaveTask = async () => {
    if (!taskForm.course_name) {
      handleShowToast("请选择或输入课程名称", "warning");
      return;
    }
    
    let updatedTasks = [...selectedUser.tasks];
    if (editingTask) {
      updatedTasks = updatedTasks.map(t => 
        t.course_name === editingTask.course_name ? taskForm : t
      );
    } else {
      if (updatedTasks.some(t => t.course_name === taskForm.course_name)) {
        handleShowToast("课程任务已存在", "warning");
        return;
      }
      updatedTasks.push(taskForm);
    }

    try {
      const res = await fetch(`${API_BASE}/api/users/${selectedUser.username}/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedTasks)
      });
      const data = await res.json();
      if (res.ok) {
        handleShowToast("任务保存成功");
        setOpenTaskDialog(false);
        fetchUsers();
      } else {
        handleShowToast(data.detail || "任务保存失败", "error");
      }
    } catch (e) {
      handleShowToast("网络请求异常", "error");
    }
  };

  const handleDeleteTask = async (courseName) => {
    if (!window.confirm(`确定删除任务 "${courseName}" 吗？`)) return;
    const updatedTasks = selectedUser.tasks.filter(t => t.course_name !== courseName);
    try {
      const res = await fetch(`${API_BASE}/api/users/${selectedUser.username}/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedTasks)
      });
      if (res.ok) {
        handleShowToast("任务删除成功");
        fetchUsers();
      } else {
        handleShowToast("删除失败", "error");
      }
    } catch (e) {
      handleShowToast("网络请求异常", "error");
    }
  };

  // Queue actions
  const handleToggleQueue = async () => {
    const nextState = !queue.active;
    try {
      const res = await fetch(`${API_BASE}/api/queue/control`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ active: nextState })
      });
      if (res.ok) {
        handleShowToast(nextState ? "队列运行已启动" : "队列已暂停运行", "info");
        fetchQueue();
      }
    } catch (e) {
      handleShowToast("队列控制失败", "error");
    }
  };

  const handleAddTaskToQueue = async (username, courseName) => {
    try {
      const res = await fetch(`${API_BASE}/api/queue/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, course_name: courseName })
      });
      const data = await res.json();
      if (res.ok) {
        handleShowToast(data.message);
        fetchQueue();
      } else {
        handleShowToast(data.detail || "加入队列失败", "error");
      }
    } catch (e) {
      handleShowToast("加入队列请求失败", "error");
    }
  };

  const handleRemoveFromQueue = async (taskId) => {
    try {
      const res = await fetch(`${API_BASE}/api/queue/remove`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: taskId })
      });
      if (res.ok) {
        handleShowToast("任务已移出队列");
        fetchQueue();
      }
    } catch (e) {
      handleShowToast("操作失败", "error");
    }
  };

  const handleToggleBrowserVisibility = async (taskId, show) => {
    if (show) {
      const ok = window.confirm("【警告提示】\n\n显示浏览器窗口后，请千万不要手动点击浏览器右上角的 “X” (关闭) 按钮！\n\n手动关闭浏览器窗口将直接导致答题任务中断崩溃。如果您需要隐藏浏览器，请再次点击列表中的眼睛图标即可。\n\n确定要显示浏览器窗口吗？");
      if (!ok) return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/queue/${taskId}/browser`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ show })
      });
      if (res.ok) {
        handleShowToast(show ? "已请求显示浏览器窗口" : "已请求隐藏浏览器窗口", "info");
        fetchQueue();
      } else {
        const data = await res.json();
        handleShowToast(data.detail || "操作失败", "error");
      }
    } catch (e) {
      handleShowToast("网络请求异常", "error");
    }
  };

  const handleSubmitManualAnswer = async (taskId) => {
    const answers = selectedAnswers[taskId] || [];
    if (answers.length === 0) {
      handleShowToast("请先选择至少一个答案", "warning");
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/queue/${taskId}/manual`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers })
      });
      if (res.ok) {
        handleShowToast("人工作答提交成功！");
        setSelectedAnswers(prev => {
          const next = { ...prev };
          delete next[taskId];
          return next;
        });
        fetchQueue();
      } else {
        const data = await res.json();
        handleShowToast(data.detail || "提交失败", "error");
      }
    } catch (e) {
      handleShowToast("网络请求异常", "error");
    }
  };

  const renderQueueStatus = (status) => {
    switch (status) {
      case 'running':
        return <Chip size="small" icon={<div className="pulse-dot" style={{ margin: '0 4px 0 8px' }} />} label="正在运行" color="secondary" variant="outlined" />;
      case 'pending':
        return <Chip size="small" icon={<PendingIcon />} label="等待中" color="warning" variant="outlined" />;
      case 'success':
        return <Chip size="small" icon={<SuccessIcon />} label="已完成" color="success" />;
      case 'failed':
        return <Chip size="small" icon={<FailedIcon />} label="失败" color="error" />;
      case 'stopped':
        return <Chip size="small" icon={<StopIcon />} label="已暂停" color="default" />;
      default:
        return <Chip size="small" label={status} />;
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', minHeight: '100vh' }}>
        
        {/* Left Drawer Navigation */}
        <Drawer
          sx={{
            width: DRAWER_WIDTH,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: DRAWER_WIDTH,
              boxSizing: 'border-box',
              background: '#0b0f19',
              borderRight: '1px solid #1e293b'
            },
          }}
          variant="permanent"
          anchor="left"
        >
          <Box sx={{ p: 3, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <Typography variant="h5" color="primary" sx={{ 
              fontFamily: 'Outfit', 
              fontWeight: 800,
              background: 'linear-gradient(to right, #a78bfa, #14b8a6)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              mb: 1
            }}>
              AutoQMYZ
            </Typography>
            <Typography variant="caption" color="text.secondary">
              智能多用户任务排队系统
            </Typography>
          </Box>
          <Divider sx={{ borderColor: '#1e293b' }} />
          <List sx={{ px: 2, py: 3 }}>
            <ListItem disablePadding sx={{ mb: 1.5 }}>
              <ListItemButton
                selected={activeTab === 'dashboard'}
                onClick={() => setActiveTab('dashboard')}
                sx={{
                  borderRadius: 2,
                  '&.Mui-selected': {
                    backgroundColor: 'rgba(167, 139, 250, 0.15)',
                    color: '#a78bfa',
                    '& .MuiListItemIcon-root': { color: '#a78bfa' }
                  }
                }}
              >
                <ListItemIcon><DashboardIcon /></ListItemIcon>
                <ListItemText primary="面板功能页" primaryTypographyProps={{ fontWeight: 500 }} />
              </ListItemButton>
            </ListItem>
            
            <ListItem disablePadding>
              <ListItemButton
                selected={activeTab === 'settings'}
                onClick={() => setActiveTab('settings')}
                sx={{
                  borderRadius: 2,
                  '&.Mui-selected': {
                    backgroundColor: 'rgba(167, 139, 250, 0.15)',
                    color: '#a78bfa',
                    '& .MuiListItemIcon-root': { color: '#a78bfa' }
                  }
                }}
              >
                <ListItemIcon><SettingsIcon /></ListItemIcon>
                <ListItemText primary="通用设置页" primaryTypographyProps={{ fontWeight: 500 }} />
              </ListItemButton>
            </ListItem>
          </List>
        </Drawer>

        {/* Main Content */}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            p: 4,
            width: `calc(100% - ${DRAWER_WIDTH}px)`,
            backgroundColor: '#0f172a'
          }}
        >
          {/* Top AppBar */}
          <AppBar
            position="sticky"
            sx={{
              background: '#1e293b',
              borderRadius: '12px',
              border: '1px solid #334155',
              boxShadow: 'none',
              mb: 4
            }}
          >
            <Toolbar sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', px: 3 }}>
              <Typography variant="h6" color="text.primary" sx={{ fontWeight: 600, m: 0 }}>
                {activeTab === 'dashboard' ? '功能控制中心' : '通用参数设置'}
              </Typography>
              
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                <Chip 
                  label={queue.active ? "队列调度：开启" : "队列调度：停止"} 
                  color={queue.active ? "success" : "default"} 
                  size="medium" 
                  sx={{ fontWeight: 600 }}
                />
              </Box>
            </Toolbar>
          </AppBar>

          {/* Tab Pages */}
          {activeTab === 'dashboard' ? (
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: 4 }}>
              
              {/* Left Side: Users list and Tasks management */}
              <Box sx={{ gridColumn: { xs: 'span 12', md: 'span 8' } }}>
                <Paper sx={{ p: 3, mb: 4, display: 'flex', flexDirection: 'column', gap: 3 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <PeopleIcon color="primary" /> 用户列表与选择
                    </Typography>
                    <Box display="flex" gap={1}>
                      <Button
                        variant="contained"
                        startIcon={<AddIcon />}
                        onClick={() => setOpenCreateUser(true)}
                        size="small"
                      >
                        创建新用户
                      </Button>
                      <IconButton onClick={fetchUsers} size="small" color="inherit">
                        <RefreshIcon />
                      </IconButton>
                    </Box>
                  </Box>

                  {/* User Selector */}
                  <FormControl fullWidth>
                    <InputLabel id="user-select-label">选择当前操作用户</InputLabel>
                    <Select
                      labelId="user-select-label"
                      value={selectedUser ? selectedUser.username : ''}
                      label="选择当前操作用户"
                      onChange={(e) => {
                        const user = users.find(u => u.username === e.target.value);
                        setSelectedUser(user || null);
                      }}
                    >
                      {users.map(u => (
                        <MenuItem key={u.username} value={u.username}>
                          <Box display="flex" justifyContent="space-between" width="100%" alignItems="center">
                            <Typography variant="body2">
                              {u.username} ({maskAccount(u.account)})
                            </Typography>
                            <Box sx={{ ml: 1 }}>
                              {u.login_status === 'verified' && (
                                <Chip size="small" label="已验证" color="success" sx={{ height: 20, fontSize: '0.75rem' }} />
                              )}
                              {u.login_status === 'failed' && (
                                <Chip size="small" label="验证失败" color="error" sx={{ height: 20, fontSize: '0.75rem' }} />
                              )}
                              {(u.login_status === 'unverified' || !u.login_status) && (
                                <Chip size="small" label="未验证" color="default" variant="outlined" sx={{ height: 20, fontSize: '0.75rem' }} />
                              )}
                            </Box>
                          </Box>
                        </MenuItem>
                      ))}
                      {users.length === 0 && (
                        <MenuItem disabled value="">
                          暂无用户，请先创建用户
                        </MenuItem>
                      )}
                    </Select>
                  </FormControl>

                  {/* Selected User Info */}
                  {selectedUser && (
                    <Card variant="outlined" sx={{ background: '#1e293b' }}>
                      <CardContent sx={{ pb: '16px !important' }}>
                        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: 2 }}>
                          <Box sx={{ gridColumn: { xs: 'span 4', sm: 'span 2' } }}>
                            <Typography variant="caption" color="text.secondary">用户名</Typography>
                            <Typography variant="body2" fontWeight="bold">{selectedUser.username}</Typography>
                          </Box>
                          <Box sx={{ gridColumn: { xs: 'span 4', sm: 'span 3' } }}>
                            <Typography variant="caption" color="text.secondary">登录账号</Typography>
                            <Typography variant="body2" fontWeight="bold">{maskAccount(selectedUser.account)}</Typography>
                          </Box>
                          <Box sx={{ gridColumn: { xs: 'span 4', sm: 'span 2' } }}>
                            <Typography variant="caption" color="text.secondary">登录状态</Typography>
                            <Box sx={{ mt: 0.5 }}>
                              {selectedUser.login_status === 'verified' && (
                                <Chip size="small" label="已验证" color="success" />
                              )}
                              {selectedUser.login_status === 'failed' && (
                                <Chip size="small" label="验证失败" color="error" />
                              )}
                              {(selectedUser.login_status === 'unverified' || !selectedUser.login_status) && (
                                <Chip size="small" label="未验证" color="default" variant="outlined" />
                              )}
                            </Box>
                          </Box>
                          <Box sx={{ gridColumn: { xs: 'span 12', sm: 'span 5' } }}>
                            <Typography variant="caption" color="text.secondary">浏览器固定UA</Typography>
                            <Typography variant="body2" noWrap sx={{ maxWidth: '100%', textOverflow: 'ellipsis', overflow: 'hidden' }} color={selectedUser.UA ? "text.primary" : "text.secondary"}>
                              {selectedUser.UA || "系统随机自动生成"}
                            </Typography>
                          </Box>
                        </Box>
                      </CardContent>
                      <CardActions sx={{ px: 2, pb: 2, justifyContent: 'flex-end', borderTop: '1px solid #334155', gap: 1 }}>
                        <Button 
                          color="secondary" 
                          startIcon={<SuccessIcon />} 
                          size="small"
                          onClick={() => handleVerifyUserLogin(selectedUser.username)}
                          disabled={verifyingUser === selectedUser.username}
                        >
                          {verifyingUser === selectedUser.username ? "正在验证..." : "验证登录"}
                        </Button>
                        <Button 
                          color="primary" 
                          startIcon={<EditIcon />} 
                          size="small"
                          onClick={handleOpenEditUser}
                          disabled={verifyingUser === selectedUser.username}
                        >
                          编辑用户
                        </Button>
                        <Button 
                          color="error" 
                          startIcon={<DeleteIcon />} 
                          size="small"
                          onClick={() => handleDeleteUser(selectedUser.username)}
                          disabled={verifyingUser === selectedUser.username}
                        >
                          删除用户
                        </Button>
                      </CardActions>
                    </Card>
                  )}
                </Paper>

                {/* Tasks management Card */}
                {selectedUser ? (
                  <Paper sx={{ p: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                      <Typography variant="h6">
                        {selectedUser.username} 的任务列表
                      </Typography>
                      <Button
                        variant="outlined"
                        startIcon={<AddIcon />}
                        onClick={handleOpenAddTask}
                        size="small"
                      >
                        添加任务课程
                      </Button>
                    </Box>

                    {/* Task cards list */}
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      {selectedUser.tasks.map((task, idx) => {
                        const progressPercent = task.aim_questions_num_total > 0 
                          ? Math.min((task.current_question_num / task.aim_questions_num_total) * 100, 100) 
                          : 0;
                        const accuracy = task.current_question_num > 0
                          ? ((task.current_right_num / task.current_question_num) * 100).toFixed(1)
                          : 0;
                        const actualRate = task.current_question_num > 0
                          ? task.current_right_num / task.current_question_num
                          : 0;
                        const isBelowRate = !task.finish && 
                          task.current_question_num > 0 && 
                          task.low_right_rate < 1 && 
                          actualRate < task.low_right_rate;
                        const qItem = queue.items.find(item => item.username === selectedUser.username && item.course_name === task.course_name);
                        const isTaskRunning = qItem?.status === 'running';

                        return (
                          <Box key={task.course_name}>
                            <Card variant="outlined" sx={{ 
                              background: task.finish 
                                ? 'rgba(16, 185, 129, 0.05)' 
                                : isBelowRate
                                  ? 'rgba(244, 63, 94, 0.03)'
                                  : task.low_right_rate === 1 
                                    ? 'rgba(245, 158, 11, 0.03)' 
                                    : '#1e293b',
                              borderColor: task.finish 
                                ? '#334155' 
                                : isBelowRate
                                  ? 'error.main'
                                  : task.low_right_rate === 1 
                                    ? 'warning.main' 
                                    : '#334155',
                              transition: 'all 0.2s',
                              '&:hover': {
                                transform: 'translateY(-2px)',
                                borderColor: isBelowRate
                                  ? 'error.main'
                                  : task.low_right_rate === 1 
                                    ? 'warning.main' 
                                    : 'primary.main'
                              }
                            }}>
                              <CardContent sx={{ pb: 1 }}>
                                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                                  <Typography variant="subtitle1" fontWeight="bold">
                                    {task.course_name}
                                  </Typography>
                                  <Box display="flex" gap={1}>
                                    {isBelowRate && (
                                      <Chip size="small" label="正确率偏低" color="error" />
                                    )}
                                    {task.low_right_rate === 1 && !task.finish && (
                                      <Chip size="small" label="仅题库作答" color="warning" />
                                    )}
                                    {task.finish ? (
                                      <Chip size="small" label="已完成" color="success" />
                                    ) : (
                                      <Chip size="small" label="进行中" color="primary" variant="outlined" />
                                    )}
                                  </Box>
                                </Box>
                                
                                {/* Progress slider */}
                                <Box mb={2}>
                                  <Box display="flex" justifyContent="space-between" mb={0.5}>
                                    <Typography variant="caption" color="text.secondary">
                                      做题进度: {task.current_question_num} / {task.aim_questions_num_total} 题
                                    </Typography>
                                    <Typography variant="caption" fontWeight="medium" color="primary">
                                      {progressPercent.toFixed(0)}%
                                    </Typography>
                                  </Box>
                                  <LinearProgress 
                                    variant="determinate" 
                                    value={progressPercent} 
                                    color={task.finish ? "success" : "primary"}
                                    sx={{ height: 6, borderRadius: 3, backgroundColor: '#0f172a' }}
                                  />
                                </Box>

                                {/* Task configurations details */}
                                <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: 2, mb: 1 }}>
                                  <Box sx={{ gridColumn: 'span 4' }}>
                                    <Typography variant="caption" color="text.secondary">做对题数</Typography>
                                    <Typography variant="body2">{task.current_right_num} 题</Typography>
                                  </Box>
                                  <Box sx={{ gridColumn: 'span 4' }}>
                                    <Typography variant="caption" color={isBelowRate ? "error.main" : "text.secondary"}>
                                      当前正确率
                                    </Typography>
                                    <Typography 
                                      variant="body2" 
                                      color={isBelowRate ? "error.main" : "secondary.main"}
                                      fontWeight={isBelowRate ? "bold" : "normal"}
                                    >
                                      {accuracy}% {isBelowRate && " (偏低)"}
                                    </Typography>
                                  </Box>
                                  <Box sx={{ gridColumn: 'span 4' }}>
                                    <Typography variant="caption" color="text.secondary">最高/低正确率限制</Typography>
                                    {task.low_right_rate === 1 ? (
                                      <Typography variant="body2" color="warning.main" fontWeight="bold">
                                        仅题库作答模式 (1.0)
                                      </Typography>
                                    ) : (
                                      <Typography variant="body2">
                                        {task.low_right_rate} ~ {task.top_right_rate}
                                      </Typography>
                                    )}
                                  </Box>
                                </Box>
                              </CardContent>

                              {/* Task card controls */}
                              <CardActions sx={{ justifyContent: 'flex-end', px: 2, pb: 2, borderTop: '1px solid #334155', gap: 1 }}>
                                <Tooltip title={isTaskRunning ? "任务正在运行，禁止编辑" : "编辑任务"}>
                                  <span>
                                    <IconButton 
                                      size="small" 
                                      color="inherit" 
                                      onClick={() => handleOpenEditTask(task)}
                                      disabled={isTaskRunning}
                                    >
                                      <EditIcon size="small" />
                                    </IconButton>
                                  </span>
                                </Tooltip>
                                <Tooltip title={isTaskRunning ? "任务正在运行，禁止删除" : "删除任务"}>
                                  <span>
                                    <IconButton 
                                      size="small" 
                                      color="error" 
                                      onClick={() => handleDeleteTask(task.course_name)}
                                      disabled={isTaskRunning}
                                    >
                                      <DeleteIcon size="small" />
                                    </IconButton>
                                  </span>
                                </Tooltip>
                                {qItem ? (
                                  <Button
                                    variant="outlined"
                                    color="error"
                                    size="small"
                                    startIcon={<DeleteIcon />}
                                    onClick={() => handleRemoveFromQueue(qItem.id)}
                                    disabled={isTaskRunning}
                                  >
                                    从队列中移除
                                  </Button>
                                ) : (
                                  <Button
                                    variant="contained"
                                    size="small"
                                    startIcon={<PlayIcon />}
                                    onClick={() => handleAddTaskToQueue(selectedUser.username, task.course_name)}
                                  >
                                    加入任务队列
                                  </Button>
                                )}
                              </CardActions>
                            </Card>
                          </Box>
                        );
                      })}
                      {selectedUser.tasks.length === 0 && (
                        <Box p={4} textAlign="center">
                          <Typography color="text.secondary">
                            该用户目前没有添加任何答题课程任务。
                          </Typography>
                        </Box>
                      )}
                    </Box>
                  </Paper>
                ) : (
                  <Paper sx={{ p: 4, textAlign: 'center' }}>
                    <Typography color="text.secondary">
                      请在上方选择或创建一个用户，以管理和配置答题课程任务。
                    </Typography>
                  </Paper>
                )}
              </Box>

              {/* Right Side: Task Queue Control Panel */}
              <Box sx={{ gridColumn: { xs: 'span 12', md: 'span 4' } }}>
                <Paper sx={{ p: 3, position: 'sticky', top: 100 }}>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                    <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <QueueIcon color="secondary" /> 任务队列
                    </Typography>
                    
                    {/* Global Queue Toggle Switch */}
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="caption" color={queue.active ? "success.main" : "text.secondary"}>
                        {queue.active ? "正在执行" : "已停止"}
                      </Typography>
                      <Switch
                        checked={queue.active}
                        onChange={handleToggleQueue}
                        color="secondary"
                      />
                    </Box>
                  </Box>

                  <Divider sx={{ borderColor: '#334155', mb: 2 }} />

                  {/* Queue items list */}
                  <List sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxHeight: 400, overflowY: 'auto' }}>
                    {queue.items.map((item) => {
                      const qActualRate = item.current_question_num > 0
                        ? item.current_right_num / item.current_question_num
                        : 0;
                      const isQBelowRate = !item.finish && 
                        item.current_question_num > 0 && 
                        item.low_right_rate < 1 && 
                        qActualRate < item.low_right_rate;

                      return (
                        <Paper 
                          key={item.id} 
                          variant="outlined" 
                          sx={{ 
                            p: 1.5, 
                            background: item.status === 'running' 
                              ? (isQBelowRate ? 'rgba(244, 63, 94, 0.08)' : 'rgba(20, 184, 166, 0.05)') 
                              : (isQBelowRate ? 'rgba(244, 63, 94, 0.03)' : '#0f172a'),
                            borderColor: isQBelowRate 
                              ? 'error.main' 
                              : item.status === 'running' 
                                ? 'secondary.main' 
                                : '#334155'
                          }}
                        >
                          <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                            <Box>
                              <Typography variant="subtitle2" fontWeight="bold">
                                {item.course_name}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                用户: {item.username}
                              </Typography>
                            </Box>
                            <Box display="flex" flexDirection="column" alignItems="flex-end" gap={0.5}>
                              {renderQueueStatus(item.status)}
                              {isQBelowRate && (
                                <Chip size="small" label="正确率偏低" color="error" sx={{ height: 18, fontSize: '0.7rem' }} />
                              )}
                            </Box>
                          </Box>

                        {/* Queue Task Logs */}
                        <Box display="flex" justifyContent="space-between" alignItems="center" mt={1}>
                          <Typography variant="caption" color="text.secondary">
                            {item.started_at ? `已启动: ${new Date(item.started_at).toLocaleTimeString()}` : `排队于: ${new Date(item.added_at).toLocaleTimeString()}`}
                          </Typography>
                          
                          <Box display="flex" gap={0.5}>
                            {item.status === 'running' && (
                              <Tooltip title={item.show_browser ? "隐藏浏览器" : "显示浏览器"}>
                                <IconButton 
                                  size="small" 
                                  color="secondary"
                                  onClick={() => handleToggleBrowserVisibility(item.id, !item.show_browser)}
                                >
                                  {item.show_browser ? <VisibilityOffIcon fontSize="small" /> : <VisibilityIcon fontSize="small" />}
                                </IconButton>
                              </Tooltip>
                            )}
                            {(item.status === 'running' || item.status === 'success' || item.status === 'failed' || item.status === 'stopped') && (
                              <Tooltip title="查看运行日志">
                                <IconButton 
                                  size="small" 
                                  color="primary"
                                  onClick={() => {
                                    setActiveLogId(item.id);
                                    fetchLogs(item.id);
                                  }}
                                >
                                  <TerminalIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            )}
                            <Tooltip title="退出队列 / 终止">
                              <IconButton 
                                size="small" 
                                color="error"
                                onClick={() => handleRemoveFromQueue(item.id)}
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </Box>
                        
                        {/* Manual Answer UI */}
                        {item.manual_question && (
                          <Paper 
                            variant="outlined" 
                            sx={{ 
                              mt: 2, 
                              p: 2, 
                              backgroundColor: 'rgba(245, 158, 11, 0.05)', 
                              borderColor: 'warning.main',
                              borderWidth: '1px',
                              borderRadius: 2
                            }}
                          >
                            <Typography variant="subtitle2" color="warning.main" fontWeight="bold" gutterBottom sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <span>⚠ 需人工作答</span>
                              <Chip size="small" color="warning" label={`剩 ${item.manual_question.remaining_time} 秒`} variant="outlined" sx={{ height: 20, fontSize: '0.75rem' }} />
                            </Typography>
                            <Typography variant="body2" sx={{ mb: 2, fontSize: '0.875rem', fontWeight: 500, whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>
                              [{item.manual_question.type}] {item.manual_question.title}
                            </Typography>
                            
                            <Box display="flex" flexDirection="column" gap={1} mb={2}>
                              {item.manual_question.options.map((opt) => {
                                const isSelected = selectedAnswers[item.id]?.includes(opt) || false;
                                const isMult = item.manual_question.type.includes("多选");
                                
                                return (
                                  <Box
                                    key={opt}
                                    onClick={() => {
                                      setSelectedAnswers(prev => {
                                        const current = prev[item.id] || [];
                                        if (isMult) {
                                          if (current.includes(opt)) {
                                            return { ...prev, [item.id]: current.filter(x => x !== opt) };
                                          } else {
                                            return { ...prev, [item.id]: [...current, opt] };
                                          }
                                        } else {
                                          return { ...prev, [item.id]: [opt] };
                                        }
                                      });
                                    }}
                                    sx={{
                                      p: 1.25,
                                      borderRadius: 1.5,
                                      border: '1px solid',
                                      borderColor: isSelected ? 'warning.main' : '#334155',
                                      backgroundColor: isSelected ? 'rgba(245, 158, 11, 0.15)' : 'rgba(30, 41, 59, 0.4)',
                                      cursor: 'pointer',
                                      transition: 'all 0.15s ease',
                                      display: 'flex',
                                      alignItems: 'center',
                                      justifyContent: 'space-between',
                                      userSelect: 'none',
                                      '&:hover': {
                                        borderColor: 'warning.main',
                                        backgroundColor: isSelected ? 'rgba(245, 158, 11, 0.2)' : 'rgba(245, 158, 11, 0.05)',
                                      }
                                    }}
                                  >
                                    <Typography variant="caption" sx={{ color: isSelected ? 'warning.main' : 'text.primary', pr: 2, flexGrow: 1 }}>
                                      {opt}
                                    </Typography>
                                    <Box
                                      sx={{
                                        width: 14,
                                        height: 14,
                                        borderRadius: isMult ? '3px' : '50%',
                                        border: '1.5px solid',
                                        borderColor: isSelected ? 'warning.main' : '#64748b',
                                        backgroundColor: isSelected ? 'warning.main' : 'transparent',
                                        transition: 'all 0.15s ease',
                                        flexShrink: 0
                                      }}
                                    />
                                  </Box>
                                );
                              })}
                            </Box>
                            
                            <Button
                              variant="contained"
                              color="warning"
                              size="small"
                              fullWidth
                              onClick={() => handleSubmitManualAnswer(item.id)}
                            >
                              提交答案
                            </Button>
                          </Paper>
                        )}
                        
                        {item.error && (
                          <Typography variant="caption" color="error" sx={{ display: 'block', mt: 1, wordBreak: 'break-all' }}>
                            错误: {item.error}
                          </Typography>
                        )}
                      </Paper>
                    )})}

                    {queue.items.length === 0 && (
                      <Box p={4} textAlign="center">
                        <Typography variant="body2" color="text.secondary">
                          队列为空，请在左侧将任务加入队列。
                        </Typography>
                      </Box>
                    )}
                  </List>
                </Paper>
              </Box>

            </Box>
          ) : (
            
            // Settings Tab View
            <Box sx={{ maxWidth: 800, mx: 'auto', display: 'flex', flexDirection: 'column', gap: 4 }}>
              <Paper sx={{ p: 4 }}>
                <Typography variant="h6" mb={4}>
                  通用参数配置 (config.toml)
                </Typography>
                
                <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: 3 }}>
                  <Box sx={{ gridColumn: 'span 12' }}>
                    <Typography variant="subtitle2" color="primary" mb={1}>AI API 配置</Typography>
                  </Box>
                  
                  <Box sx={{ gridColumn: 'span 12' }}>
                    <TextField
                      fullWidth
                      label="API Key (密钥)"
                      value={config.api_key}
                      type="password"
                      onChange={(e) => setConfig({ ...config, api_key: e.target.value })}
                    />
                  </Box>

                  <Box sx={{ gridColumn: { xs: 'span 12', md: 'span 6' } }}>
                    <TextField
                      fullWidth
                      label="Base URL (接口基础地址)"
                      value={config.base_url}
                      onChange={(e) => setConfig({ ...config, base_url: e.target.value })}
                    />
                  </Box>

                  <Box sx={{ gridColumn: { xs: 'span 12', md: 'span 6' } }}>
                    <TextField
                      fullWidth
                      label="Model Name (使用的模型)"
                      value={config.model}
                      onChange={(e) => setConfig({ ...config, model: e.target.value })}
                    />
                  </Box>

                  <Box sx={{ gridColumn: 'span 12' }}>
                    <Divider sx={{ borderColor: '#334155', my: 2 }} />
                    <Typography variant="subtitle2" color="primary" mb={1}>系统并行并发限制</Typography>
                  </Box>

                  <Box sx={{ gridColumn: { xs: 'span 12', md: 'span 6' } }}>
                    <TextField
                      fullWidth
                      label="全局任务最大并行数 (task_parallel_limit)"
                      type="number"
                      value={config.task_parallel_limit}
                      onChange={(e) => setConfig({ ...config, task_parallel_limit: parseInt(e.target.value) || 1 })}
                      helperText="限制系统同时运行的总任务线程数 (并发数)"
                    />
                  </Box>

                  <Box sx={{ gridColumn: { xs: 'span 12', md: 'span 6' } }}>
                    <TextField
                      fullWidth
                      label="单用户最大并行数 (user_parallel_limit)"
                      type="number"
                      value={config.user_parallel_limit}
                      onChange={(e) => setConfig({ ...config, user_parallel_limit: parseInt(e.target.value) || 1 })}
                      helperText="限制同一个用户下同时运行的课程数，多余的会排队等待"
                    />
                  </Box>

                  <Box sx={{ gridColumn: 'span 12' }}>
                    <Divider sx={{ borderColor: '#334155', my: 2 }} />
                    <Typography variant="subtitle2" color="primary" mb={1}>自动答题优先机制设置 (上下移动调整优先级)</Typography>
                  </Box>

                  <Box sx={{ gridColumn: 'span 12' }}>
                    <Paper variant="outlined" sx={{ p: 2, background: '#0f172a', borderColor: '#334155' }}>
                      <List sx={{ p: 0 }}>
                        {(config.answer_priority || ['db', 'ai', 'manual', 'random']).map((strategy, index) => (
                          <ListItem
                            key={strategy}
                            divider={index < (config.answer_priority || []).length - 1}
                            sx={{ py: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                          >
                            <Box display="flex" alignItems="center" gap={2}>
                              <Chip label={index + 1} size="small" color="primary" sx={{ fontWeight: 'bold' }} />
                              <ListItemText 
                                primary={STRATEGY_NAMES[strategy] || strategy}
                                primaryTypographyProps={{ variant: 'body2', fontWeight: 500 }}
                              />
                            </Box>
                            <Box display="flex" gap={0.5}>
                              <IconButton
                                size="small"
                                disabled={index === 0}
                                onClick={() => {
                                  const newPriority = [...config.answer_priority];
                                  const temp = newPriority[index];
                                  newPriority[index] = newPriority[index - 1];
                                  newPriority[index - 1] = temp;
                                  setConfig({ ...config, answer_priority: newPriority });
                                }}
                              >
                                <ArrowUpwardIcon fontSize="small" />
                              </IconButton>
                              <IconButton
                                size="small"
                                disabled={index === (config.answer_priority || []).length - 1}
                                onClick={() => {
                                  const newPriority = [...config.answer_priority];
                                  const temp = newPriority[index];
                                  newPriority[index] = newPriority[index + 1];
                                  newPriority[index + 1] = temp;
                                  setConfig({ ...config, answer_priority: newPriority });
                                }}
                              >
                                <ArrowDownwardIcon fontSize="small" />
                              </IconButton>
                            </Box>
                          </ListItem>
                        ))}
                      </List>
                    </Paper>
                  </Box>

                  <Box sx={{ gridColumn: { xs: 'span 12', md: 'span 6' } }}>
                    <TextField
                      fullWidth
                      label="人工作答等待超时时间 (秒)"
                      type="number"
                      value={config.manual_timeout || 30}
                      onChange={(e) => setConfig({ ...config, manual_timeout: parseInt(e.target.value) || 0 })}
                      helperText="在人工作答模式下，如果在规定秒数内未在控制台输入答案，将自动跳过并执行后面的策略"
                    />
                  </Box>

                  <Box sx={{ gridColumn: 'span 12', display: 'flex', justifyContent: 'flex-end', mt: 3 }}>
                    <Button
                      variant="contained"
                      size="large"
                      startIcon={<PowerIcon />}
                      onClick={handleSaveConfig}
                    >
                      保存配置
                    </Button>
                  </Box>
                </Box>
              </Paper>

              <Paper sx={{ p: 4 }}>
                <Typography variant="h6" mb={2} color="primary" sx={{ fontWeight: 600 }}>
                  系统日志与空间管理
                </Typography>
                <Typography variant="body2" color="text.secondary" mb={3}>
                  系统运行时会产生日志文件，主要包括系统运行日志与各任务的具体执行日志。系统默认会自动轮转保留最近 7 天的日志，并会在启动时自动清理 7 天前未修改的历史日志。你也可以在此手动清理。
                </Typography>
                
                <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: 3, mb: 3 }}>
                  <Box sx={{ gridColumn: { xs: 'span 12', sm: 'span 4' } }}>
                    <Paper variant="outlined" sx={{ p: 2, textAlign: 'center', background: '#0f172a', borderColor: '#334155' }}>
                      <Typography variant="caption" color="text.secondary" display="block">系统核心日志大小</Typography>
                      <Typography variant="h6" color="text.primary" sx={{ mt: 1, fontWeight: 'bold' }}>{logStats.system_log_size || '0 B'}</Typography>
                    </Paper>
                  </Box>
                  <Box sx={{ gridColumn: { xs: 'span 12', sm: 'span 4' } }}>
                    <Paper variant="outlined" sx={{ p: 2, textAlign: 'center', background: '#0f172a', borderColor: '#334155' }}>
                      <Typography variant="caption" color="text.secondary" display="block">任务过程日志大小</Typography>
                      <Typography variant="h6" color="text.primary" sx={{ mt: 1, fontWeight: 'bold' }}>{logStats.task_logs_size || '0 B'}</Typography>
                    </Paper>
                  </Box>
                  <Box sx={{ gridColumn: { xs: 'span 12', sm: 'span 4' } }}>
                    <Paper variant="outlined" sx={{ p: 2, textAlign: 'center', background: '#0f172a', borderColor: '#334155' }}>
                      <Typography variant="caption" color="text.secondary" display="block">任务日志文件个数</Typography>
                      <Typography variant="h6" color="text.primary" sx={{ mt: 1, fontWeight: 'bold' }}>{logStats.task_logs_count || 0} 个</Typography>
                    </Paper>
                  </Box>
                </Box>

                <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
                  <Button
                    variant="outlined"
                    startIcon={<RefreshIcon />}
                    onClick={fetchLogStats}
                  >
                    刷新统计
                  </Button>
                  <Button
                    variant="contained"
                    color="error"
                    startIcon={<DeleteIcon />}
                    onClick={() => setOpenClearLogsConfirm(true)}
                  >
                    立即清理历史日志
                  </Button>
                </Box>
              </Paper>
            </Box>
          )}
        </Box>

        {/* ---------------- Dialogs ---------------- */}
        
        {/* Clear Logs Confirmation Dialog */}
        <Dialog open={openClearLogsConfirm} onClose={() => setOpenClearLogsConfirm(false)}>
          <DialogTitle>确认清理系统日志</DialogTitle>
          <DialogContent>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              确定要清理所有历史日志吗？这将清除所有非运行中任务的日志文件和系统日志备份文件，并重置当前的 app.log 文件。此操作不可撤销。
            </Typography>
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 2.5 }}>
            <Button onClick={() => setOpenClearLogsConfirm(false)}>取消</Button>
            <Button onClick={handleClearLogs} variant="contained" color="error">确认清理</Button>
          </DialogActions>
        </Dialog>
        
        {/* Create User Dialog */}
        <Dialog open={openCreateUser} onClose={() => setOpenCreateUser(false)}>
          <DialogTitle>创建新自动化用户</DialogTitle>
          <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, minWidth: 320, pt: '10px !important' }}>
            <TextField
              label="用户名称"
              fullWidth
              value={newUser.username}
              onChange={(e) => setNewUser({ ...newUser, username: e.target.value.replace(/[^a-zA-Z0-9_]/g, '') })}
              helperText="仅支持英文/拼音/数字，用于保存文件名"
            />
            <TextField
              label="手机账号"
              fullWidth
              value={newUser.account}
              onChange={(e) => setNewUser({ ...newUser, account: e.target.value })}
            />
            <TextField
              label="登录密码"
              fullWidth
              type="password"
              value={newUser.password}
              onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
            />
            <TextField
              label="自动登录免验链接 (verify_request)"
              fullWidth
              value={newUser.verify_request}
              onChange={(e) => setNewUser({ ...newUser, verify_request: e.target.value })}
              helperText="免验证直接登录的URL，可选填"
            />
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 3 }}>
            <Button onClick={() => setOpenCreateUser(false)} color="inherit">取消</Button>
            <Button onClick={handleCreateUser} variant="contained">确认创建</Button>
          </DialogActions>
        </Dialog>

        {/* Edit User Dialog */}
        <Dialog open={openEditUser} onClose={() => setOpenEditUser(false)}>
          <DialogTitle>编辑用户资料 ({selectedUser?.username})</DialogTitle>
          <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, minWidth: 340, pt: '10px !important' }}>
            <TextField
              label="手机账号"
              fullWidth
              value={editUserForm.account}
              onChange={(e) => setEditUserForm({ ...editUserForm, account: e.target.value })}
            />
            <TextField
              label="登录密码 (留空则不修改)"
              fullWidth
              type="password"
              placeholder="••••••••"
              value={editUserForm.password}
              onChange={(e) => setEditUserForm({ ...editUserForm, password: e.target.value })}
            />
            <TextField
              label="自动登录免验链接 (verify_request)"
              fullWidth
              value={editUserForm.verify_request}
              onChange={(e) => setEditUserForm({ ...editUserForm, verify_request: e.target.value })}
            />
            <TextField
              label="浏览器固定 UA (浏览器标识)"
              fullWidth
              value={editUserForm.UA}
              onChange={(e) => setEditUserForm({ ...editUserForm, UA: e.target.value })}
              helperText="留空则由系统自动生成并保存"
            />
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 3 }}>
            <Button onClick={() => setOpenEditUser(false)} color="inherit">取消</Button>
            <Button onClick={handleSaveEditUser} variant="contained">保存修改</Button>
          </DialogActions>
        </Dialog>

        {/* Task Form Dialog (Add/Edit) */}
        <Dialog open={openTaskDialog} onClose={() => setOpenTaskDialog(false)}>
          <DialogTitle>{editingTask ? '编辑课程任务' : '添加课程任务'}</DialogTitle>
          <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2.5, minWidth: 360, pt: '10px !important' }}>
            {editingTask ? (
              <TextField
                label="课程"
                fullWidth
                disabled
                value={taskForm.course_name}
              />
            ) : (
              <Autocomplete
                freeSolo
                options={selectedUser?.verified_courses || []}
                getOptionLabel={(option) => {
                  if (typeof option === 'string') return option;
                  return option.name || '';
                }}
                renderOption={(props, option) => {
                  const { key, ...optionProps } = props;
                  return (
                    <li key={key || option.name} {...optionProps}>
                      <Box display="flex" justifyContent="space-between" width="100%" alignItems="center">
                        <Typography variant="body2" fontWeight="medium">
                          {option.name}
                        </Typography>
                        <Chip 
                          size="small" 
                          label={option.exists ? `${option.question_count} 题已录入` : "未录入题库"} 
                          color={option.exists ? "success" : "default"} 
                          variant={option.exists ? "filled" : "outlined"}
                          sx={{ ml: 2, height: 22 }}
                        />
                      </Box>
                    </li>
                  );
                }}
                value={selectedUser?.verified_courses?.find(c => c.name === taskForm.course_name) || taskForm.course_name}
                onChange={(event, newValue) => {
                  const val = typeof newValue === 'string' ? newValue : newValue?.name || '';
                  setTaskForm({ ...taskForm, course_name: val });
                }}
                onInputChange={(event, newInputValue) => {
                  setTaskForm({ ...taskForm, course_name: newInputValue || '' });
                }}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="课程"
                    fullWidth
                    placeholder="输入或选择课程名称"
                    helperText="建议从您已验证的线上课程列表中选择，会标明题库中包含的题目数"
                  />
                )}
              />
            )}
            <TextField
              label="总共需答题数"
              type="number"
              fullWidth
              value={taskForm.aim_questions_num_total}
              onChange={(e) => setTaskForm({ ...taskForm, aim_questions_num_total: parseInt(e.target.value) || 0 })}
            />
            
            <TextField
              label="最低正确率"
              type="number"
              fullWidth
              inputProps={{ step: 0.05 }}
              value={taskForm.low_right_rate}
              onChange={(e) => setTaskForm({ ...taskForm, low_right_rate: parseFloat(e.target.value) || 0 })}
              helperText={taskForm.low_right_rate === 1 ? "【已开启仅题库作答】未录入将自动刷新" : "设置正确率下限。设为 1 开启仅题库"}
            />
            <TextField
              label="最高正确率"
              type="number"
              fullWidth
              inputProps={{ step: 0.05 }}
              value={taskForm.top_right_rate}
              onChange={(e) => setTaskForm({ ...taskForm, top_right_rate: parseFloat(e.target.value) || 0 })}
              helperText="高于此比率会故意做错"
            />

            <TextField
              label="每题最少用时 (秒)"
              type="number"
              fullWidth
              value={taskForm.min_question_time}
              onChange={(e) => setTaskForm({ ...taskForm, min_question_time: parseFloat(e.target.value) || 0 })}
            />

            <Box display="flex" gap={2}>
              <TextField
                label="当前答题进度"
                type="number"
                value={taskForm.current_question_num}
                onChange={(e) => setTaskForm({ ...taskForm, current_question_num: parseInt(e.target.value) || 0 })}
              />
              <TextField
                label="当前回答正确题数"
                type="number"
                value={taskForm.current_right_num}
                onChange={(e) => setTaskForm({ ...taskForm, current_right_num: parseInt(e.target.value) || 0 })}
              />
            </Box>

            <FormControlLabel
              control={
                <Switch
                  checked={taskForm.finish}
                  onChange={(e) => {
                    const checked = e.target.checked;
                    if (!checked && taskForm.finish) {
                      if (window.confirm("确定要取消标记已完成吗？这将会同时清除该任务的所有做题进度！")) {
                        setTaskForm({
                          ...taskForm,
                          finish: false,
                          current_question_num: 0,
                          current_right_num: 0
                        });
                      }
                    } else {
                      setTaskForm({ ...taskForm, finish: checked });
                    }
                  }}
                />
              }
              label="标记任务已完成"
            />
          </DialogContent>
          <DialogActions sx={{ px: 3, pb: 3 }}>
            <Button onClick={() => setOpenTaskDialog(false)} color="inherit">取消</Button>
            <Button onClick={handleSaveTask} variant="contained">保存修改</Button>
          </DialogActions>
        </Dialog>

        {/* Live logs stream dialog */}
        <Dialog 
          open={!!activeLogId} 
          onClose={() => setActiveLogId(null)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">运行终端日志 (实时)</Typography>
            <Chip label={activeLogId} size="small" color="secondary" />
          </DialogTitle>
          <DialogContent sx={{ p: 0, backgroundColor: '#020617', borderTop: '1px solid #1e293b' }}>
            <Box 
              sx={{ 
                p: 2, 
                maxHeight: 450, 
                minHeight: 300, 
                overflowY: 'auto', 
                fontFamily: 'Consolas, monospace',
                fontSize: 13,
                lineHeight: 1.6,
                color: '#e2e8f0',
                whiteSpace: 'pre-wrap'
              }}
            >
              {activeLogContent}
              <div ref={logEndRef} />
            </Box>
          </DialogContent>
          <DialogActions sx={{ p: 2, backgroundColor: '#090d16', borderTop: '1px solid #1e293b' }}>
            <Button onClick={() => {
              if (activeLogId) fetchLogs(activeLogId);
            }} startIcon={<RefreshIcon />}>刷新</Button>
            <Button onClick={() => setActiveLogId(null)} variant="contained">关闭</Button>
          </DialogActions>
        </Dialog>

        {/* Notifications Alert */}
        <Snackbar
          open={toast.open}
          autoHideDuration={4000}
          onClose={() => setToast({ ...toast, open: false })}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        >
          <Alert severity={toast.severity} onClose={() => setToast({ ...toast, open: false })}>
            {toast.message}
          </Alert>
        </Snackbar>

      </Box>
    </ThemeProvider>
  );
}

export default App;
