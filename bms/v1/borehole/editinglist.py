# -*- coding: utf-8 -*-
from bms.v1.action import Action
import math


class ListEditingBorehole(Action):

    async def execute(
            self, limit=None, page=None,
            filter={}, orderby=None, direction=None
        ):

        paging = ''

        where, params = self.filterBorehole(filter)

        if limit is not None and page is not None:
            paging = """
                LIMIT %s
                OFFSET %s
            """ % (self.getIdx(), self.getIdx())
            params += [
                limit, (int(limit) * (int(page) - 1))
            ]

        rowsSql = """
            SELECT
                borehole.id_bho as id,
                (
                    select row_to_json(t)
                    FROM (
                        SELECT
                            author.id_usr as id,
                            author.username as username,
                            to_char(
                                created_bho,
                                'YYYY-MM-DD"T"HH24:MI:SS'
                            ) as date
                    ) t
                ) as author,
                original_name_bho as original_name,
                kind_id_cli as kind,
                restriction_id_cli as restriction,
                to_char(
                    restriction_until_bho,
                    'YYYY-MM-DD'
                ) as restriction_until,
                location_x_bho as location_x,
                location_y_bho as location_y,
                srs_id_cli as srs,
                elevation_z_bho as elevation_z,
                hrs_id_cli as hrs,
                drilling_date_bho as drilling_date,
                length_bho as length,
                (
                    select row_to_json(t)
                    FROM (
                        SELECT
                            status_id_cli as status
                    ) t
                ) as extended,
                stratigraphy as stratigraphy,
                completness.percentage
            FROM
                borehole
            INNER JOIN public.completness
            ON completness.id_bho = borehole.id_bho
            INNER JOIN public.users as author
                ON author_id = author.id_usr
            LEFT JOIN (
                SELECT
                    id_bho_fk,
                    array_to_json(
                        array_agg(
                            json_build_object(
                                'id', id,
                                'kind', kind,
                                'layers', layers
                            )
                        )
                    ) AS stratigraphy
                FROM (
                    SELECT
                        id_bho_fk,
                        id_sty AS id,
                        kind_id_cli AS kind,
                        COUNT(id_lay) AS layers
                    FROM
                        stratigraphy
                    INNER JOIN codelist
                        ON kind_id_cli = id_cli
                    LEFT JOIN layer
                        ON id_sty_fk = id_sty
                    GROUP BY id_bho_fk, id_sty, id_cli
                    ORDER BY id_bho_fk, order_cli
                ) t
                GROUP BY id_bho_fk
            ) AS strt
            ON strt.id_bho_fk = borehole.id_bho
        """

        cntSql = """
            SELECT count(*) AS cnt
            FROM borehole
            INNER JOIN public.completness
            ON completness.id_bho = borehole.id_bho
        """

        if len(where) > 0:
            rowsSql += """
                WHERE %s
            """ % " AND ".join(where)
            cntSql += """
                WHERE %s
            """ % " AND ".join(where)

        _orderby, direction = self.getordering(orderby, direction)

        sql = """
            SELECT
                array_to_json(
                    array_agg(
                        row_to_json(t)
                    )
                ),
                COALESCE((
                    %s
                ), 0)
            FROM (
                %s
            ORDER BY %s %s NULLS LAST
                %s
            ) AS t
        """ % (
            cntSql,
            rowsSql,
            _orderby,
            direction,
            paging
        )

        # print (sql, params)

        rec = await self.conn.fetchrow(
            sql, *(params)
        )
        return {
            "data": self.decode(rec[0]) if rec[0] is not None else [],
            "orderby": orderby,
            "direction": direction,
            "page": page if page is not None else 1,
            "pages": math.ceil(rec[1]/limit) if limit is not None else 1,
            "rows": rec[1]
        }