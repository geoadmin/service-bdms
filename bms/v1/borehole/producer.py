# -*- coding: utf-8 -*-S
from bms.v1.handlers import Producer
from bms.v1.borehole import (
    CheckBorehole,
    CreateBorehole,
    DeleteBorehole,
    ListEditingBorehole,
    MultiPatchBorehole,
    PatchBorehole
)
from bms.v1.setting import (
    PatchSetting
)


class BoreholeProducerHandler(Producer):
    async def execute(self, request):
        action = request.pop('action', None)

        if action in [
                'CREATE',
                'DELETE',
                'PATCH',
                'MULTIPATCH',
                'CHECK',
                'LIST']:

            async with self.pool.acquire() as conn:

                exe = None

                if action == 'CREATE':
                    exe = CreateBorehole(conn)
                    request['user_id'] = self.user['id']

                if action == 'DELETE':
                    exe = DeleteBorehole(conn)

                elif action == 'PATCH':
                    exe = PatchBorehole(conn)
                    request['user_id'] = self.user['id']

                elif action == 'MULTIPATCH':
                    exe = MultiPatchBorehole(conn)
                    request['user_id'] = self.user['id']

                elif action == 'CHECK':
                    exe = CheckBorehole(conn)
                
                if action == 'LIST':
                    exe = ListEditingBorehole(conn)

                    # update only if ordering changed
                    if 'orderby' in request and (
                        request['orderby'] is not None
                    ) and (
                        self.user[
                            'setting'
                        ]['eboreholetable']['orderby'] != request['orderby']
                    ):
                        await (PatchSetting(conn)).execute(
                            self.user['id'],
                            'eboreholetable.orderby',
                            request['orderby']
                        )
                    else:
                        request['orderby'] = self.user[
                            'setting'
                        ]['eboreholetable']['orderby']

                    if 'direction' in request and (
                        request['direction'] is not None
                    ) and (
                        self.user[
                            'setting'
                        ]['eboreholetable']['direction'] != request['direction']
                    ):
                        await (PatchSetting(conn)).execute(
                            self.user['id'],
                            'eboreholetable.direction',
                            request['direction']
                        )
                    else:
                        request['direction'] = self.user[
                            'setting'
                        ]['eboreholetable']['direction']

                request.pop('lang', None)

                if exe is not None:
                    return (
                        await exe.execute(**request)
                    )

        raise Exception("Action '%s' unknown" % action)