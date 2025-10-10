#include <bits/stdc++.h>
using namespace std;

// ======= Thông số ảnh =======
const double lonLeft = 105.840676;
const double lonRight = 105.861112;
const double latTop = 21.041218;
const double latBottom = 21.023721;
const int WIDTH = 8500;
const int HEIGHT = 7801;

struct Node {
    double x, y;
};

// ======= GPS -> Pixel =======
Node gpsToPixel(double lat, double lon) {
    Node n;
    n.x = (lon - lonLeft) / (lonRight - lonLeft) * WIDTH;
    n.y = (latTop - lat) / (latTop - latBottom) * HEIGHT;
    return n;
}

// ======= Xử lý từng file =======
void processFile(const string &filename,
                 unordered_map<string, Node> &allNodes,
                 unordered_set<string> &validNodeIds,
                 set<pair<string, string>> &edges)
{
    ifstream fin(filename);
    if (!fin.is_open()) {
        cerr << "Không thể mở file " << filename << "\n";
        return;
    }

    string line;
    bool inWay = false;
    bool isHighway = false;
    vector<string> refs;

    while (getline(fin, line)) {
        line.erase(0, line.find_first_not_of(" \t\r\n"));

        // --- NODE ---
        if (line.find("<node ") != string::npos) {
            size_t idPos = line.find("id=\"");
            size_t latPos = line.find("lat=\"");
            size_t lonPos = line.find("lon=\"");

            if (idPos != string::npos && latPos != string::npos && lonPos != string::npos) {
                string id = line.substr(idPos + 4, line.find("\"", idPos + 4) - (idPos + 4));
                string latStr = line.substr(latPos + 5, line.find("\"", latPos + 5) - (latPos + 5));
                string lonStr = line.substr(lonPos + 5, line.find("\"", lonPos + 5) - (lonPos + 5));
                double lat = stod(latStr);
                double lon = stod(lonStr);
                Node n = gpsToPixel(lat, lon);

                // Lọc node ngoài ảnh
                if (n.x >= 0 && n.y >= 0 && n.x <= WIDTH && n.y <= HEIGHT) {
                    allNodes[id] = n;
                }
            }
        }

        // --- WAY ---
        else if (line.find("<way ") != string::npos) {
            inWay = true;
            isHighway = false;
            refs.clear();
        }
        else if (inWay && line.find("<nd ref=") != string::npos) {
            size_t p1 = line.find("\"");
            size_t p2 = line.find("\"", p1 + 1);
            if (p1 != string::npos && p2 != string::npos) {
                string ref = line.substr(p1 + 1, p2 - p1 - 1);
                refs.push_back(ref);
            }
        }
        else if (inWay && line.find("<tag") != string::npos && line.find("k=\"highway\"") != string::npos) {
            isHighway = true;
        }
        else if (inWay && line.find("</way>") != string::npos) {
            if (isHighway) {
                for (auto &r : refs) validNodeIds.insert(r);
                for (size_t i = 0; i + 1 < refs.size(); ++i) {
                    if (refs[i] != refs[i + 1])
                        edges.insert({refs[i], refs[i + 1]});
                }
            }
            inWay = false;
            refs.clear();
        }

        // --- RELATION ---
        else if (line.find("<relation") != string::npos) {
            // bỏ qua toàn bộ khối relation
            while (getline(fin, line)) {
                if (line.find("</relation>") != string::npos) break;
            }
        }
    }
    fin.close();
}

// ======= MAIN =======
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    unordered_map<string, Node> allNodes;
    unordered_set<string> validNodeIds;
    set<pair<string, string>> edges;

    // Xử lý cả 2 file bản đồ
    processFile("map1.txt", allNodes, validNodeIds, edges);
    processFile("map2.txt", allNodes, validNodeIds, edges);

    // Ghi nodes.txt
    ofstream fn("nodes.txt");
    for (const auto &id : validNodeIds) {
        if (allNodes.count(id)) {
            const Node &n = allNodes[id];
            fn << id << " " << fixed << setprecision(4) << n.x << " " << n.y << "\n";
        }
    }
    fn.close();

    // Ghi edges.txt (chỉ cạnh hợp lệ)
    ofstream fe("edges.txt");
    for (const auto &e : edges) {
        const string &from = e.first;
        const string &to = e.second;
        if (allNodes.count(from) && allNodes.count(to) &&
            validNodeIds.count(from) && validNodeIds.count(to)) {
            const Node &a = allNodes.at(from);
            const Node &b = allNodes.at(to);
            double dx = a.x - b.x, dy = a.y - b.y;
            double dist = sqrt(dx * dx + dy * dy) / 100.0;
            fe << from << " " << to << " " << fixed << setprecision(4) << dist << "\n";
        }
    }
    fe.close();

    cout << "✅ Hoàn thành! Đã xuất nodes.txt và edges.txt\n";
    return 0;
}
