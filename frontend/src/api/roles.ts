/**
 * TalentFlow AI — Roles Catalog API Client
 */
import client from './client';

export interface RoleItem {
  id: string;
  name: string;
  slug: string;
  occupational_class: string;
  description: string;
  aliases: string[];
  required_skills_default: string[];
  experience_level: string;
  active: boolean;
}

export const rolesApi = {
  getRoles: async (params?: { occupational_class?: string; search?: string }): Promise<RoleItem[]> => {
    const res = await client.get('/roles', { params });
    return res.data || res.roles || [];
  },
};

