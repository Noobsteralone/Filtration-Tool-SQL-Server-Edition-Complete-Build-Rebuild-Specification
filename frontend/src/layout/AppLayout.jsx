import React from "react";
import { Layout, Menu, Avatar, Dropdown, Typography } from "antd";
import {
  DashboardOutlined,
  FilterOutlined,
  DiffOutlined,
  DatabaseOutlined,
  GlobalOutlined,
  UnorderedListOutlined,
  ScheduleOutlined,
  SettingOutlined,
  TeamOutlined,
  FileSearchOutlined,
  UserOutlined,
  LogoutOutlined,
} from "@ant-design/icons";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext.jsx";

const { Header, Sider, Content } = Layout;

const NAV_ITEMS = [
  { key: "/", icon: <DashboardOutlined />, label: "Dashboard" },
  { key: "/filtration", icon: <FilterOutlined />, label: "Filtration" },
  { key: "/duplicate-tld-check", icon: <DiffOutlined />, label: "Duplicate / TLD Check" },
  { key: "/master-files", icon: <DatabaseOutlined />, label: "Master Files" },
  { key: "/other-tld-master", icon: <GlobalOutlined />, label: "Other TLD Master" },
  { key: "/reference-lists", icon: <UnorderedListOutlined />, label: "Reference Lists", minRole: "ADMIN" },
  { key: "/jobs", icon: <ScheduleOutlined />, label: "Jobs" },
  { key: "/settings", icon: <SettingOutlined />, label: "Settings", minRole: "ADMIN" },
  { key: "/users", icon: <TeamOutlined />, label: "Users", minRole: "SUPER_ADMIN" },
  { key: "/activity-logs", icon: <FileSearchOutlined />, label: "Activity Logs", minRole: "ADMIN" },
];

export default function AppLayout() {
  const { user, logout, hasRole } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const visibleItems = NAV_ITEMS.filter((item) => !item.minRole || hasRole(item.minRole));

  const userMenu = {
    items: [{ key: "logout", icon: <LogoutOutlined />, label: "Log out" }],
    onClick: ({ key }) => {
      if (key === "logout") {
        logout();
        navigate("/login");
      }
    },
  };

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider breakpoint="lg" collapsedWidth="0" theme="light">
        <div style={{ padding: "16px", fontWeight: 700, fontSize: 18, color: "#1a56db" }}>FT Filtration Tool</div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname === "/" ? "/" : `/${location.pathname.split("/")[1]}`]}
          items={visibleItems.map((item) => ({
            key: item.key,
            icon: item.icon,
            label: <Link to={item.key}>{item.label}</Link>,
          }))}
        />
      </Sider>
      <Layout>
        <Header style={{ background: "#fff", display: "flex", justifyContent: "flex-end", alignItems: "center", padding: "0 24px" }}>
          <Dropdown menu={userMenu} placement="bottomRight">
            <span style={{ cursor: "pointer" }}>
              <Avatar icon={<UserOutlined />} style={{ marginRight: 8 }} />
              <Typography.Text>{user?.username}</Typography.Text>
              <Typography.Text type="secondary" style={{ marginLeft: 8 }}>
                ({user?.role})
              </Typography.Text>
            </span>
          </Dropdown>
        </Header>
        <Content style={{ margin: 24 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
