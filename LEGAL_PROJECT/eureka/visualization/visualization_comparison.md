# So sánh Neo4j Bloom và Custom Matplotlib Renderer

| Tiêu chí | Neo4j Bloom | Matplotlib (Custom Renderer) |
|---|---|---|
| **Nguồn dữ liệu** | Trực tiếp từ CSDL Neo4j qua Cypher query | File script Python (dữ liệu được hardcode tĩnh từ Cypher) |
| **Khả năng chứng minh KG thật** | **Tuyệt đối**. Thể hiện UI của Neo4j, có search bar, thanh công cụ thật. Giám khảo tin tưởng 100%. | Kém hơn. Vì vẽ bằng thư viện bên thứ 3 nên giám khảo có thể nghi ngờ đồ thị được "vẽ tay" hoặc hardcode. |
| **Khả năng tùy chỉnh layout** | Hạn chế. Neo4j Bloom tự động dùng thuật toán Force-directed (hoặc Hierarchical), không thể chỉnh chính xác tọa độ từng node/chữ (dễ bị đè chữ). | **Tuyệt đối**. Kiểm soát tọa độ đến từng pixel, xử lý 100% tình trạng chồng chéo nhãn (overlap). |
| **Dùng cho slide** | Khá ổn nhưng màu sắc phụ thuộc vào cấu hình perspective, độ phân giải bị giới hạn bởi màn hình (screenshot). | **Cực kỳ tối ưu**. Xuất ảnh vector/PNG siêu nét (300+ DPI), bố cục Academic chuẩn mực, chú thích đầy đủ. |

## Recommendation (Đề xuất)
**Nên sử dụng Custom Matplotlib Renderer cho Slide chính, và chuẩn bị Neo4j Bloom ở chế độ Live Demo.**

- **Lý do:** Hình ảnh từ Matplotlib cực kỳ sắc nét, rõ ràng, sạch sẽ và hoàn toàn không bị chồng lấn chữ (Overlap) — yếu tố sống còn cho một Academic Presentation.
- Tuy nhiên, để vượt qua câu hỏi phản biện *"Đây có phải graph thật không?"*, bạn hãy đưa ảnh Neo4j Bloom Screenshot vào slide Phụ lục (Appendix), hoặc mở trực tiếp Neo4j Bloom lên máy chiếu để chứng minh dữ liệu đang "sống" trong Database thực sự.
