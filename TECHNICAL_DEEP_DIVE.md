# 核心技术深度解析文档 (答辩专用)

本文档详细拆解了项目中的核心技术难点与实现原理，专门用于回答答辩评委的深层技术提问。

---

## 1. 会话管理机制 (Session Management)

### **Q: 你们是如何在无状态的 HTTP 协议中区分不同用户的连续对话的？**

**核心方案**：基于 UUID 的自定义 Session 鉴权机制。

**技术细节**：
1.  **唯一标识符 (Identity)**：
    *   我们不依赖浏览器的 Cookie Session，而是为每个对话生成一个 **UUIDv4**（全球唯一标识符），例如 `550e8400-e29b...`。
    *   数据库表 `ChatSession` 的主键即为此 UUID。

2.  **通信协议 (Protocol)**：
    *   前端在发起 `/chat/` 请求时，会将当前会话 ID 放入自定义 HTTP Header 中：`X-Chat-Session-ID: <uuid>`。
    *   后端中间件/视图函数直接从 Header 读取 ID，而不是解析 Cookie，这样设计使得 API 更加无状态化（Stateless），便于未来扩展到移动端或第三方调用。

3.  **上下文关联 (Context)**：
    *   利用 **LangChain** 的 `RunnableWithMessageHistory` 类。
    *   每次请求到达时，LangChain 会自动根据 `session_id` 去 MySQL 数据库查找最近的 `k` 轮 `ChatMessage`。
    *   这些历史记录被组装进 System Prompt，从而让大模型拥有“记忆”。

---

## 2. 流式响应技术 (Streaming Response)

### **Q: 为什么选择 StreamingHTTP 而不是 WebSocket 来实现“打字机”效果？**

**技术选型对比**：

| 特性 | StreamingHTTP (本项目采用) | WebSocket |
| :--- | :--- | :--- |
| **通信模型** | Request-Response (单向流) | Full-Duplex (全双工) |
| **连接成本** | 低 (标准 HTTP) | 高 (需协议升级握手) |
| **防火墙/代理** | 友好 (穿透性强) | 可能被拦截 |
| **适用场景** | 生成式 AI、视频流 | 即时通讯、即时游戏 |

**决策依据**：
1.  **场景匹配度**：用户与 AI 的对话本质上是“一问一答”模式。用户提问后，服务器持续返回数据直到结束，中间不需要用户干预。这完全符合 HTTP 流式传输的定义。
2.  **架构轻量化**：WebSocket 需要维护长连接心跳，且 Django 需要引入 `Channels` 和 Redis，架构复杂度高。而 `StreamingHttpResponse` 是 Django 原生功能，无需额外依赖，开发维护效率极高。

**代码实现**：
后端使用 Python 生成器 (`yield`) 逐步产出 LLM 生成的 Token，前端通过 `fetch` API 的 `ReadableStream` 读取分块数据，从而实现毫秒级的首字响应延迟。

---

## 3. 人脸识别算法 (Face Recognition Algorithm)

### **Q: 人脸识别是如何判断“是不是同一个人”的？**

**核心算法**：**ResNet (深度残差网络) + 欧几里得距离 (Euclidean Distance)**

**实现流程**：
1.  **检测 (Detection)**：使用 HOG (方向梯度直方图) 算法在图像中定位人脸坐标 (Top, Right, Bottom, Left)。
2.  **特征映射 (Embedding)**：将人脸图像输入预训练的深度神经网络，输出一个 **128 维的特征向量**。这个向量对光照、姿态有一定的不变性。
3.  **距离计算 (Metric)**：
    *   在 128 维欧氏空间中，计算“当前人脸向量”与“数据库已知人脸向量”之间的直线距离。
    *   公式：$d(p, q) = \sqrt{\sum_{i=1}^{128} (q_i - p_i)^2}$
4.  **阈值判定 (Threshold)**：
    *   本项目设定阈值为 **0.45**。
    *   若 $Distance < 0.45$，判定为**匹配成功**。
    *   若 $Distance \ge 0.45$，判定为**匹配失败**。
    *   *数据支撑：0.45 是我们在测试中平衡误识率 (FAR) 和拒识率 (FRR) 后得出的经验最优值。*

---

## 4. 前后端数据可视化 (Data Visualization)

### **Q: 统计大屏的数据是如何处理和适配的？**

**后端聚合 (Backend Aggregation)**：
*   为了避免把成千上万条日志拉到内存中处理，我们充分利用了 **数据库 (SQL) 的计算能力**。
*   使用 Django ORM 的 `annotate` 和 `TruncDate` 函数，直接在数据库层面按天分组并计数：
    ```python
    # 生成 SELECT date(created_at), COUNT(id) ... GROUP BY date(created_at) 的高效 SQL
    ChatMessage.objects.annotate(date=TruncDate('created_at')).values('date').annotate(count=Count('id'))
    ```

**前端适配 (Frontend Responsive)**：
*   **Flexbox 布局**：采用 `flex: 1` 自动填充剩余空间策略，解决了“大屏留白，小屏截断”的适配难题。
*   **ECharts Resize**：监听 `window.resize` 事件，调用 `echartsInstance.resize()`，确保图表在窗口缩放时重绘，保证任何分辨率下不失真。

---

## 5. 总结 (Conclusion)

本项目虽然界面简洁，但在底层技术上做到了**逻辑闭环**与**工程化落地**：
1.  **安全**：人脸特征向量化存储，不存原图，保障隐私。
2.  **性能**：流式传输解决大模型响应慢的痛点；数据库聚合解决统计慢的痛点。
3.  **扩展**：基于 UUID 和 Header 的会话管理，为未来扩展 API 网关或移动端打下了基础。
