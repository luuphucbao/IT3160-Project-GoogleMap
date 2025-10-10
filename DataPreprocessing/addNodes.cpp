#include <bits/stdc++.h>
using namespace std;
typedef long long ll;

struct Node {
    double x, y;
};

double distanceEuclid(const Node &a, const Node &b) {
    double dx = a.x - b.x, dy = a.y - b.y;
    return sqrt(dx * dx + dy * dy) / 100.0; // chia 100 như yêu cầu
}
const double limit=0.06;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string nodesFile = "nodes.txt";
    string edgesFile = "edges.txt";
    string newNodesFile = "newNodes.txt";
    string newEdgesFile = "newEdges.txt";


    // ======= Đọc nodes =======
    unordered_map<ll, Node> nodes;
    ifstream finNodes(nodesFile);
    ll id; double x, y;
    while (finNodes >> id >> x >> y) {
        nodes[id] = {x, y};
    }
    finNodes.close();

    // ======= Đọc edges =======
    struct Edge { ll u, v; };
    vector<Edge> edges;
    ifstream finEdges(edgesFile);
    ll u, v; double w;
    while (finEdges >> u >> v >> w) {
        edges.push_back({u, v});
    }
    finEdges.close();

    // ======= Xử lý chia nhỏ =======
    vector<pair<ll, Node>> newNodes;
    vector<tuple<ll,ll,double>> newEdges;

    // lưu các node cũ
    for (auto &[id, n] : nodes) newNodes.push_back({id, n});

    ll nextId = 1;
    // for (auto &[id, _] : nodes)
    //     nextId = max(nextId, id + 1);

    for (auto &e : edges) {
        Node A = nodes[e.u], B = nodes[e.v];
        double dist = distanceEuclid(A, B);
        if (dist <= limit) {
            newEdges.push_back({e.u, e.v, dist});
        } else {
            int k = ceil(dist / limit);
            vector<pair<ll,Node>> path;
            path.push_back({e.u,nodes[e.u]});

            for (int i = 1; i < k; i++) {
                double t = (double)i / k;
                Node mid;
                mid.x = A.x + t * (B.x - A.x);
                mid.y = A.y + t * (B.y - A.y);
                ll newId = nextId++;
                newNodes.push_back({newId, mid});
                path.push_back({newId,mid});
            }
            path.push_back({e.v,nodes[e.v]});
            for (int i = 0; i  < path.size()-1; i++) {
                Node p1=path[i].second;
                Node p2=path[i+1].second;
                double w = distanceEuclid(p1, p2);
                newEdges.push_back({path[i].first, path[i+1].first, w});
            }
        }
    }

    // ======= Ghi file =======
    ofstream foutNodes(newNodesFile);
    for (auto &[id, n] : newNodes)
        foutNodes << id << " " << fixed << setprecision(4) << n.x << " " << n.y << "\n";
    foutNodes.close();

    ofstream foutEdges(newEdgesFile);
    for (auto &[a, b, w] : newEdges)
        foutEdges << a << " " << b << " " << fixed << setprecision(4) << w << "\n";
    foutEdges.close();

    cout << "Hoan thanh. Ket qua luu tai:\n";
    cout << " - " << newNodesFile << "\n";
    cout << " - " << newEdgesFile << "\n";
    return 0;
}
