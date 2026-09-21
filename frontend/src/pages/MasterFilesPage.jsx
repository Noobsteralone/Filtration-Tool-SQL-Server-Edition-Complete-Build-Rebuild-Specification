import React, { useEffect, useState } from "react";
import { Alert, Button, Card, Input, Popconfirm, Table, Tabs, Typography, message } from "antd";
import { SearchOutlined } from "@ant-design/icons";
import { apiClient, friendlyError } from "../api/client.js";
import { useAuth } from "../auth/AuthContext.jsx";

export default function MasterFilesPage() {
  const { hasRole } = useAuth();
  const [search, setSearch] = useState("");
  const [emails, setEmails] = useState([]);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function loadEmails(searchTerm) {
    setLoading(true);
    apiClient
      .get("/api/master", { params: { search: searchTerm || undefined, page: 1, page_size: 100 } })
      .then((res) => setEmails(res.data))
      .catch((err) => setError(friendlyError(err, "Could not search Master.")))
      .finally(() => setLoading(false));
  }

  function loadFiles() {
    apiClient
      .get("/api/master/files")
      .then((res) => setFiles(res.data))
      .catch(() => {});
  }

  useEffect(() => {
    loadEmails("");
    loadFiles();
  }, []);

  async function deleteFile(id) {
    try {
      await apiClient.delete(`/api/master/files/${id}`);
      message.success("Removed from Master file listing.");
      loadFiles();
    } catch (err) {
      message.error(friendlyError(err, "Could not delete."));
    }
  }

  const emailColumns = [
    { title: "Email", dataIndex: "Email" },
    { title: "Name", dataIndex: "Name" },
    { title: "Company", dataIndex: "Company" },
    { title: "Title", dataIndex: "Title" },
    { title: "Industry", dataIndex: "Industry" },
    { title: "Country", dataIndex: "Country" },
    { title: "Source File", dataIndex: "SourceFile" },
    { title: "Added", dataIndex: "CreatedAt", render: (v) => new Date(v).toLocaleDateString() },
  ];

  const fileColumns = [
    { title: "File Name", dataIndex: "FileName" },
    { title: "Rows Added", dataIndex: "RowsAdded" },
    { title: "Rows Duplicate", dataIndex: "RowsDuplicate" },
    { title: "Uploaded", dataIndex: "CreatedAt", render: (v) => new Date(v).toLocaleString() },
    hasRole("ADMIN") && {
      title: "Actions",
      render: (_, record) => (
        <Popconfirm title="Remove this file's association from Master?" onConfirm={() => deleteFile(record.MasterFileID)}>
          <Button size="small" danger>
            Delete
          </Button>
        </Popconfirm>
      ),
    },
  ].filter(Boolean);

  return (
    <div>
      <Typography.Title level={3}>Master Files</Typography.Title>
      {error && <Alert type="error" message={error} style={{ marginBottom: 16 }} />}
      <Tabs
        items={[
          {
            key: "emails",
            label: "Master Email Dataset",
            children: (
              <Card>
                <Input.Search
                  placeholder="Search by email, company, name, title, industry, or source file"
                  allowClear
                  enterButton={<SearchOutlined />}
                  style={{ maxWidth: 480, marginBottom: 16 }}
                  onSearch={(value) => {
                    setSearch(value);
                    loadEmails(value);
                  }}
                />
                <Table rowKey="MasterID" loading={loading} dataSource={emails} columns={emailColumns} />
              </Card>
            ),
          },
          {
            key: "files",
            label: "Contributing Files",
            children: (
              <Card>
                <Table rowKey="MasterFileID" dataSource={files} columns={fileColumns} />
              </Card>
            ),
          },
        ]}
      />
    </div>
  );
}
