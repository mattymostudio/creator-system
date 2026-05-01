#!/usr/bin/env python3
"""
Relationship Graph Builder — builds a network graph from email co-correspondent
data across all three accounts.

Uses the co_correspondents field from enriched CSVs and thread data from bundles
to build edges between contacts.

Usage:
    python3 build_relationship_graph.py <bundles_dirs...> <output_dir>
"""

import json
import csv
import glob
import os
import sys
from collections import defaultdict
from datetime import datetime


MATTS_EMAILS = {
    'you@yourcompany.example', 'you@yourcompany.example',
    'you@yourdomain.example', 'you-personal@example.com',
    'you@yourcompany.example', 'your-handle@gmail.example',
    'you-work2@example.com', 'you-work3@example.com',
    'you-work4@example.com', 'you-sampleb@example.com',
    'you-work@example.com', 'info@yourdomain.example',
    'team@yourcompany.example',
}


def build_graph(bundle_dirs, output_dir):
    # Load all bundles
    all_bundles = {}

    for bdir in bundle_dirs:
        for bf in sorted(glob.glob(os.path.join(bdir, '*.json'))):
            basename = os.path.basename(bf)
            if any(x in basename for x in ['megabatch', 'results_', 'batch_', 'manifest']):
                continue
            try:
                with open(bf) as f:
                    bundle = json.load(f)
            except:
                continue
            if 'email' not in bundle:
                continue

            email = bundle['email'].lower()
            if email in MATTS_EMAILS:
                continue

            # Merge if same email across accounts
            if email in all_bundles:
                existing = all_bundles[email]
                existing['total_emails'] = existing.get('total_emails', 0) + bundle.get('total_emails', 0)
                existing['source_accounts'] = existing.get('source_accounts', set())
                existing['source_accounts'].add(bundle.get('source_account', '?'))
                # Keep the richer enrichment
                if bundle.get('enrichment') and not existing.get('enrichment'):
                    existing['enrichment'] = bundle['enrichment']
                    existing['matched'] = bundle.get('matched', {})
            else:
                bundle['source_accounts'] = {bundle.get('source_account', '?')}
                all_bundles[email] = bundle

    print(f"Loaded {len(all_bundles)} unique contacts across all accounts")

    # Build nodes
    nodes = {}
    for email, bundle in all_bundles.items():
        enrichment = bundle.get('enrichment') or {}
        matched = bundle.get('matched', {})

        name = matched.get('best_name', '')
        if not name and bundle.get('display_names'):
            name = bundle['display_names'][0]
        if not name:
            name = email.split('@')[0]

        nodes[email] = {
            'id': email,
            'name': name,
            'email': email,
            'org': matched.get('best_org', '') or '',
            'relationship_type': enrichment.get('relationship_type', '') or '',
            'total_emails': bundle.get('total_emails', 0),
            'first_contact': (bundle.get('first_contact') or '')[:10],
            'last_contact': (bundle.get('last_contact') or '')[:10],
            'projects': enrichment.get('projects_in_common', []) or [],
            'source_accounts': list(bundle.get('source_accounts', set())),
            'vault_page': matched.get('vault_match', ''),
        }

    # Build edges from thread co-occurrence
    # Each bundle has threads — contacts that appear on the same thread
    # share an edge. We approximate this from unique_subjects:
    # if two contacts have the same subject line, they likely share a thread.

    subject_to_contacts = defaultdict(set)
    for email, bundle in all_bundles.items():
        subjects = bundle.get('unique_subjects', [])
        for subj in subjects:
            # Normalize subject for matching
            norm_subj = subj.strip().lower()
            if len(norm_subj) > 10:  # Skip very short/generic subjects
                subject_to_contacts[norm_subj].add(email)

    # Build edge weights
    edges = defaultdict(lambda: {'weight': 0, 'shared_subjects': []})

    for subj, contacts in subject_to_contacts.items():
        if len(contacts) < 2 or len(contacts) > 20:  # Skip solo or mass threads
            continue

        contacts_list = sorted(contacts)
        for i in range(len(contacts_list)):
            for j in range(i + 1, len(contacts_list)):
                edge_key = (contacts_list[i], contacts_list[j])
                edges[edge_key]['weight'] += 1
                if len(edges[edge_key]['shared_subjects']) < 5:
                    edges[edge_key]['shared_subjects'].append(subj[:80])

    print(f"Built {len(edges)} edges from shared subject lines")

    # Filter to significant edges (weight >= 2 or both contacts are enriched)
    significant_edges = {}
    for (a, b), data in edges.items():
        if data['weight'] >= 2:
            significant_edges[(a, b)] = data
        elif a in nodes and b in nodes:
            # Keep single-weight edges between high-volume contacts
            if nodes[a]['total_emails'] >= 20 and nodes[b]['total_emails'] >= 20:
                significant_edges[(a, b)] = data

    print(f"Significant edges (weight >= 2 or high-volume pair): {len(significant_edges)}")

    # Compute connection counts and top connections per node
    connection_counts = defaultdict(int)
    top_connections = defaultdict(list)

    for (a, b), data in significant_edges.items():
        connection_counts[a] += 1
        connection_counts[b] += 1
        top_connections[a].append((b, data['weight']))
        top_connections[b].append((a, data['weight']))

    # Sort top connections by weight
    for email in top_connections:
        top_connections[email].sort(key=lambda x: x[1], reverse=True)

    # Compute bridge score (contacts who connect otherwise-separate clusters)
    # Simple heuristic: contacts with connections to multiple orgs/relationship types
    bridge_scores = {}
    for email, conns in top_connections.items():
        connected_orgs = set()
        connected_types = set()
        for conn_email, weight in conns[:20]:
            if conn_email in nodes:
                org = nodes[conn_email].get('org', '')
                rtype = nodes[conn_email].get('relationship_type', '')
                if org:
                    connected_orgs.add(org)
                if rtype:
                    connected_types.add(rtype)
        bridge_scores[email] = len(connected_orgs) * 2 + len(connected_types)

    # Write graph JSON
    graph = {
        'nodes': list(nodes.values()),
        'edges': [
            {
                'source': a,
                'target': b,
                'weight': data['weight'],
                'shared_subjects': data['shared_subjects'],
            }
            for (a, b), data in significant_edges.items()
        ],
        'stats': {
            'total_nodes': len(nodes),
            'total_edges': len(significant_edges),
            'generated': datetime.now().isoformat(),
        }
    }

    graph_path = os.path.join(output_dir, 'relationship_graph.json')
    with open(graph_path, 'w') as f:
        json.dump(graph, f, indent=2, ensure_ascii=False)

    # Write edge CSV
    edge_csv_path = os.path.join(output_dir, 'relationship_edges.csv')
    with open(edge_csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'contact_a_email', 'contact_a_name', 'contact_b_email', 'contact_b_name',
            'shared_threads', 'sample_subjects'
        ])
        writer.writeheader()
        for (a, b), data in sorted(significant_edges.items(), key=lambda x: x[1]['weight'], reverse=True):
            writer.writerow({
                'contact_a_email': a,
                'contact_a_name': nodes.get(a, {}).get('name', ''),
                'contact_b_email': b,
                'contact_b_name': nodes.get(b, {}).get('name', ''),
                'shared_threads': data['weight'],
                'sample_subjects': ' | '.join(data['shared_subjects'][:3]),
            })

    # Write top connections summary
    summary_path = os.path.join(output_dir, 'top_connectors.csv')
    with open(summary_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'email', 'name', 'total_connections', 'bridge_score',
            'total_emails', 'relationship_type', 'top_5_connections'
        ])
        writer.writeheader()
        for email, count in sorted(connection_counts.items(), key=lambda x: x[1], reverse=True)[:500]:
            node = nodes.get(email, {})
            top5 = [f"{nodes.get(c, {}).get('name', c)}({w})" for c, w in top_connections[email][:5]]
            writer.writerow({
                'email': email,
                'name': node.get('name', ''),
                'total_connections': count,
                'bridge_score': bridge_scores.get(email, 0),
                'total_emails': node.get('total_emails', 0),
                'relationship_type': node.get('relationship_type', ''),
                'top_5_connections': ', '.join(top5),
            })

    print(f"\nWritten:")
    print(f"  {graph_path} ({len(graph['nodes'])} nodes, {len(graph['edges'])} edges)")
    print(f"  {edge_csv_path}")
    print(f"  {summary_path}")

    # Top 20 connectors
    print(f"\nTop 20 connectors (most shared threads with other contacts):")
    for email, count in sorted(connection_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
        node = nodes.get(email, {})
        print(f"  {count:>4} connections  {node.get('name', ''):<35} {node.get('relationship_type', '')}")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 build_relationship_graph.py <bundles_dir1> [dir2...] <output_dir>")
        sys.exit(1)

    bundle_dirs = sys.argv[1:-1]
    output_dir = sys.argv[-1]
    os.makedirs(output_dir, exist_ok=True)
    build_graph(bundle_dirs, output_dir)
