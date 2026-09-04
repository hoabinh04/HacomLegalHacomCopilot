from verified_rag import VerifiedLegalRAG
from alert_engine import LegalAlertEngine
from rules_engine import LegalRulesEngine

def test_queries():
    print("=" * 60)
    print("🧪 CHƯƠNG TRÌNH KIỂM THỬ THỰC TẾ MÔ HÌNH HACOM LEGAL COPILOT")
    print("=" * 60)
    
    rag = VerifiedLegalRAG()
    alert_sys = LegalAlertEngine()
    rules = LegalRulesEngine()

    # Test 1: Bồi thường GPMB
    q1 = "Thủ tục bồi thường GPMB khi thu hồi đất quy định như thế nào?"
    print(f"\n❓ [TEST 1] Hỏi: '{q1}'")
    res1 = rag.ask_legal(q1, "KĐT")
    print(f"📌 Trích dẫn nguồn ({len(res1['citations'])} mục):")
    for c in res1['citations']:
        print(f"   - {c['citation']} ({c['doc_name'][:40]}...)")
    print(f"💬 Trợ lý AI trả lời:\n{res1['answer'][:300]}...\n")

    # Test 2: Rules Engine kiểm tra lợi nhuận NOXH
    print("❓ [TEST 2] Rules Engine: Kiểm tra điều kiện lợi nhuận định mức 9.5% cho NOXH Hacom GalaCity:")
    check_res = rules.check_noxh_profit_limit(9.5)
    print("   -> Kết quả:", check_res)

    # Test 3: Alert Engine phân tích tác động Luật mới
    print("\n❓ [TEST 3] Alert Engine: Đánh giá tác động khi Nghị định 71/2024/NĐ-CP về giá đất ban hành:")
    alert_res = alert_sys.assess_new_law_impact("71/2024/NĐ-CP", "Nghị định 71/2024/NĐ-CP quy định về giá đất", "Đất đai")
    print("   -> Mức độ cảnh báo:", alert_res["severity"])
    print("   -> Dự án bị ảnh hưởng:", [p["name"] for p in alert_res["affected_projects"]])
    print("   -> Lời khuyên hành động:", alert_res["recommended_action"])

    print("\n" + "=" * 60)
    print("✅ HOÀN THÀNH KIỂM THỬ MÔ HÌNH HACOM LEGAL COPILOT THÀNH CÔNG!")
    print("=" * 60)

if __name__ == "__main__":
    test_queries()
